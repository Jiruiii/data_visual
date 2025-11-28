from flask import Flask, render_template, jsonify, request
import pandas as pd
import json
import os

# 載入 .env 檔案
try:
    from dotenv import load_dotenv

    if os.path.exists(".env"):
        load_dotenv()
        print("✓ 已載入 .env 環境變數")
except ImportError:
    pass

app = Flask(__name__)


def download_kaggle_dataset():
    """從 Kaggle 下載資料集"""
    try:
        print("正在嘗試使用 Kaggle API 下載資料集...")

        kaggle_username = os.environ.get("KAGGLE_USERNAME")
        kaggle_key = os.environ.get("KAGGLE_KEY")

        if kaggle_username and kaggle_key:
            print("✓ 從環境變數讀取 Kaggle 憑證")
            os.environ["KAGGLE_USERNAME"] = kaggle_username
            os.environ["KAGGLE_KEY"] = kaggle_key
        elif os.path.exists("kaggle.json"):
            print("✓ 找到專案內的 kaggle.json")
            os.environ["KAGGLE_CONFIG_DIR"] = os.path.abspath(".")

        import kaggle

        kaggle.api.dataset_download_files(
            "atharvasoundankar/global-cybersecurity-threats-2015-2024",
            path="data/",
            unzip=True,
        )
        print("✓ 成功從 Kaggle 下載資料集")
        return True
    except Exception as e:
        print(f"! 無法從 Kaggle 下載: {e}")
        return False


def load_data():
    """載入網路安全威脅資料集"""
    if download_kaggle_dataset():
        data_dir = "data"
        csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
        if csv_files:
            data_path = os.path.join(data_dir, csv_files[0])
            print(f"✓ 找到資料檔案: {data_path}")

            df = pd.read_csv(data_path)
            print(f"✓ 成功載入 {len(df)} 筆資料")
            print(f"資料欄位: {list(df.columns)}")

            # 資料前處理
            if "Year" in df.columns:
                df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

            return df
    return pd.DataFrame()


# 載入資料
df_global = load_data()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/overview")
def overview():
    return render_template("overview.html")


@app.route("/map")
def map_view():
    return render_template("map.html")


@app.route("/charts")
def charts():
    return render_template("charts.html")


@app.route("/advanced")
def advanced():
    return render_template("advanced.html")


@app.route("/api/map_data")
def get_map_data():
    """地圖：各國網路攻擊事件數量（返回原始資料）"""
    try:
        df = df_global.copy()

        required_cols = ['Country', 'Year', 'Financial Loss (in Million $)']
        for col in required_cols:
            if col not in df.columns:
                return jsonify({"error":
                                f"Required column '{col}' not found"}), 400

        df_clean = df.dropna(subset=required_cols)

        country_year_loss = df_clean.groupby(
            ['Country',
             'Year'])['Financial Loss (in Million $)'].sum().reset_index()
        country_year_loss.columns = ['Country', 'Year', 'Loss']

        country_year_loss['Year'] = country_year_loss['Year'].astype(int)
        country_year_loss = country_year_loss.sort_values(['Year', 'Country'])

        # 計算每個國家的總損失（用於排序）
        total_loss_by_country = df_clean.groupby(
            'Country')['Financial Loss (in Million $)'].sum().reset_index()
        total_loss_by_country.columns = ['Country', 'TotalLoss']

        # 取得所有年份和國家
        all_years = sorted(country_year_loss['Year'].unique().tolist())
        all_countries = country_year_loss['Country'].unique().tolist()

        # 為每個年份準備資料
        data_by_year = {}
        for year in all_years:
            year_data = country_year_loss[country_year_loss['Year'] == year]
            data_by_year[str(year)] = {
                'countries': year_data['Country'].tolist(),
                'losses': year_data['Loss'].tolist()
            }

        # 計算全局統計資訊
        statistics = {
            'total_loss':
            float(df_clean['Financial Loss (in Million $)'].sum()),
            'avg_loss_per_country':
            float(total_loss_by_country['TotalLoss'].mean()),
            'max_loss_country':
            total_loss_by_country.nlargest(1,
                                           'TotalLoss')['Country'].values[0],
            'max_loss_value':
            float(
                total_loss_by_country.nlargest(
                    1, 'TotalLoss')['TotalLoss'].values[0]),
            'year_range':
            f"{min(all_years)} - {max(all_years)}",
            'total_countries':
            len(all_countries)
        }

        return jsonify({
            'years': all_years,
            'data_by_year': data_by_year,
            'all_countries': all_countries,
            'statistics': statistics
        })
    except Exception as e:
        print(f"Map API Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route("/api/industry_analysis")
def get_industry_analysis():
    """長條圖：產業類型分析（攻擊次數或財務損失）"""
    try:
        df = df_global.copy()
        chart_type = request.args.get("type", "count")

        if chart_type == "count":
            # 按產業統計攻擊次數
            industry_counts = df["Target Industry"].value_counts().reset_index(
            )
            industry_counts.columns = ["Industry", "Count"]

            return jsonify({
                "labels": industry_counts["Industry"].tolist(),
                "values": industry_counts["Count"].tolist(),
                "type": "count",
            })
        else:  # loss
            # 按產業統計財務損失
            industry_loss = (
                df.groupby("Target Industry")
                ["Financial Loss (in Million $)"].sum().reset_index())
            industry_loss = industry_loss.sort_values(
                "Financial Loss (in Million $)", ascending=True)

            return jsonify({
                "labels":
                industry_loss["Target Industry"].tolist(),
                "values":
                industry_loss["Financial Loss (in Million $)"].tolist(),
                "type":
                "loss",
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/countries")
def get_countries():
    """取得所有可用的國家列表"""
    try:
        df = df_global.copy()
        countries = sorted(df["Country"].unique().tolist())
        return jsonify({"countries": countries})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/top_ips")
def get_top_ips():
    """長條圖：TOP N 受影響使用者最多的事件（支援國家篩選）"""
    try:
        df = df_global.copy()

        country = request.args.get("country", "all")
        top_n = int(request.args.get("top_n", 10))

        if country != "all":
            df = df[df["Country"] == country]

        if df.empty:
            return jsonify({
                "labels": [],
                "values": [],
                "countries": [],
                "attack_types": [],
                "statistics": {
                    "total_events": 0,
                    "total_users": 0,
                    "avg_impact": 0,
                },
                "country": country,
                "top_n": top_n,
            })

        top_incidents = df.nlargest(top_n, "Number of Affected Users")[[
            "Country", "Attack Type", "Number of Affected Users"
        ]]

        statistics = {
            "total_events": len(df),
            "total_users": int(df["Number of Affected Users"].sum()),
            "avg_impact": float(df["Number of Affected Users"].mean()),
        }

        return jsonify({
            "labels": (top_incidents["Country"] + " - " +
                       top_incidents["Attack Type"]).tolist(),
            "values":
            top_incidents["Number of Affected Users"].tolist(),
            "countries":
            top_incidents["Country"].tolist(),
            "attack_types":
            top_incidents["Attack Type"].tolist(),
            "statistics":
            statistics,
            "country":
            country,
            "top_n":
            top_n,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/time_series")
def get_time_series():
    """折線圖：年度攻擊趨勢（支援單一國家或多國比較，包含財務損失）"""
    try:
        df = df_global.copy()

        country = request.args.get("country", "all")
        countries_param = request.args.get("countries", "")
        mode = request.args.get("mode", "single")

        if mode == "compare" and countries_param:
            # 多國比較模式
            countries = [
                c.strip() for c in countries_param.split(",") if c.strip()
            ]

            result = {"mode": "compare", "countries": [], "series": []}

            for country_name in countries[:5]:
                country_df = df[df["Country"] == country_name]
                if not country_df.empty:
                    yearly_counts = (
                        country_df.groupby("Year").size().reset_index(
                            name="Count"))
                    result["series"].append({
                        "country":
                        country_name,
                        "years":
                        yearly_counts["Year"].tolist(),
                        "counts":
                        yearly_counts["Count"].tolist(),
                    })

            return jsonify(result)

        else:
            # 單一國家或全球模式（加上財務損失）
            if country != "all":
                df = df[df["Country"] == country]

            if df.empty:
                return jsonify({
                    "mode": "single",
                    "country": country,
                    "years": [],
                    "counts": [],
                    "losses": [],
                    "statistics": {},
                })

            # 計算每年的攻擊次數和財務損失
            yearly_stats = (df.groupby("Year").agg({
                "Country":
                "count",
                "Financial Loss (in Million $)":
                "sum"
            }).reset_index())
            yearly_stats.columns = ["Year", "Count", "Loss"]

            # 計算統計數據
            total = yearly_stats["Count"].sum()
            average = yearly_stats["Count"].mean()
            total_loss = yearly_stats["Loss"].sum()
            avg_loss = yearly_stats["Loss"].mean()

            # 計算趨勢（首尾年份增長率）
            if len(yearly_stats) >= 2:
                first_year_count = yearly_stats.iloc[0]["Count"]
                last_year_count = yearly_stats.iloc[-1]["Count"]
                trend = ((
                    (last_year_count - first_year_count) / first_year_count) *
                         100 if first_year_count > 0 else 0)

                first_year_loss = yearly_stats.iloc[0]["Loss"]
                last_year_loss = yearly_stats.iloc[-1]["Loss"]
                loss_trend = ((
                    (last_year_loss - first_year_loss) / first_year_loss) *
                              100 if first_year_loss > 0 else 0)
            else:
                trend = 0
                loss_trend = 0

            statistics = {
                "total": int(total),
                "average": float(average),
                "trend": float(trend),
                "total_loss": float(total_loss),
                "avg_loss": float(avg_loss),
                "loss_trend": float(loss_trend),
            }

            return jsonify({
                "mode": "single",
                "country": country,
                "years": yearly_stats["Year"].tolist(),
                "counts": yearly_stats["Count"].tolist(),
                "losses": yearly_stats["Loss"].tolist(),
                "statistics": statistics,
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/attack_types")
def get_attack_types():
    """圓餅圖：攻擊類型分布"""
    try:
        df = df_global.copy()

        country = request.args.get("country", "all")
        if country != "all":
            df = df[df["Country"] == country]

        attack_counts = df["Attack Type"].value_counts().reset_index()
        attack_counts.columns = ["Attack_Type", "Count"]

        return jsonify({
            "labels": attack_counts["Attack_Type"].tolist(),
            "values": attack_counts["Count"].tolist(),
            "country": country,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/heatmap")
def get_heatmap():
    """熱力圖：平均財務損失 by 目標產業 & 攻擊類型"""
    try:
        df = df_global.copy()

        required_cols = [
            'Target Industry', 'Attack Type', 'Financial Loss (in Million $)'
        ]
        for col in required_cols:
            if col not in df.columns:
                return jsonify({'error': f'Missing column: {col}'}), 400

        df_clean = df.dropna(subset=required_cols)

        if df_clean.empty:
            return jsonify({
                'industries': [],
                'attack_types': [],
                'heatmap_data': [],
                'statistics': {}
            })

        heatmap_df = df_clean.groupby([
            'Target Industry', 'Attack Type'
        ])['Financial Loss (in Million $)'].mean().reset_index()
        heatmap_df.columns = ['Industry', 'Attack', 'AvgLoss']

        # 使用 pivot_table 轉換為矩陣格式
        pivot_table = heatmap_df.pivot(index='Industry',
                                       columns='Attack',
                                       values='AvgLoss')

        # 填充缺失值為 0（某些產業可能沒有某些攻擊類型）
        pivot_table = pivot_table.fillna(0)

        # 按總損失排序產業（讓高風險產業在上方）
        industry_totals = pivot_table.sum(axis=1).sort_values(ascending=False)
        pivot_table = pivot_table.loc[industry_totals.index]

        # 按總損失排序攻擊類型（讓高危攻擊在左側）
        attack_totals = pivot_table.sum(axis=0).sort_values(ascending=False)
        pivot_table = pivot_table[attack_totals.index]

        # 轉換為 list of lists（每一行是一個產業）
        industries = pivot_table.index.tolist()
        attack_types = pivot_table.columns.tolist()
        heatmap_data = pivot_table.values.tolist()

        # 計算統計資訊
        max_loss_idx = pivot_table.stack().idxmax()
        min_loss_idx = pivot_table.stack().idxmin()

        statistics = {
            'max_loss': {
                'industry': max_loss_idx[0],
                'attack': max_loss_idx[1],
                'value': float(pivot_table.loc[max_loss_idx])
            },
            'min_loss': {
                'industry': min_loss_idx[0],
                'attack': min_loss_idx[1],
                'value': float(pivot_table.loc[min_loss_idx])
            },
            'total_combinations': len(heatmap_df),
            'avg_loss_overall': float(heatmap_df['AvgLoss'].mean()),
            'total_industries': len(industries),
            'total_attack_types': len(attack_types)
        }

        return jsonify({
            'industries': industries,
            'attack_types': attack_types,
            'heatmap_data': heatmap_data,
            'statistics': statistics
        })

    except Exception as e:
        print(f"Heatmap API Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route("/api/treemap")
def get_treemap():
    """Treemap：目標產業與攻擊類型分布"""
    try:
        df = df_global.copy()
        
        labels = []
        parents = []
        values = []
        
        # 第一層：產業統計
        industry_counts = df.groupby("Target Industry").size().reset_index(name="Count")
        industry_counts = industry_counts[industry_counts["Count"] > 5]
        
        valid_industries = set(industry_counts["Target Industry"].tolist())
        
        # 收集產業數據
        industry_values = []
        for _, row in industry_counts.iterrows():
            labels.append(row["Target Industry"])
            parents.append("All Industries")
            values.append(int(row["Count"]))
            industry_values.append(int(row["Count"]))
        
        # 第二層：產業下的攻擊類型
        industry_attack = df.groupby(["Target Industry", "Attack Type"]).size().reset_index(name="Count")
        industry_attack = industry_attack[industry_attack["Count"] > 5]
        
        industry_acronyms = {
            "IT": "IT",
            "Healthcare": "HC",
            "Education": "EDU",
            "Government": "GOV",
            "Banking": "BANK",
            "Retail": "RET",
            "Telecommunications": "TEL",
        }

        for _, row in industry_attack.iterrows():
            industry = str(row["Target Industry"]).strip()
            attack = str(row["Attack Type"]).strip()
            
            if industry in valid_industries:
                label = f"{industry_acronyms.get(industry)} - {attack}"
                labels.append(label)
                parents.append(industry)
                values.append(int(row["Count"]))

        
        # 添加根節點
        labels.insert(0, "All Industries")
        parents.insert(0, "")
        values.insert(0, sum(industry_values))
        
        return jsonify({
            "labels": labels,
            "parents": parents,
            "values": values
        })
        
    except Exception as e:
        print(f"Treemap API Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/severity_by_type")
def get_severity_by_type():
    """攻擊類型與安全漏洞分析"""
    try:
        df = df_global.copy()

        # 統計攻擊類型與安全漏洞類型
        vuln_data = (df.groupby(["Attack Type", "Security Vulnerability Type"
                                 ]).size().reset_index(name="Count"))
        vuln_data = vuln_data.nlargest(30, "Count")

        # 取得所有唯一的攻擊類型和漏洞類型
        attack_types = vuln_data["Attack Type"].unique().tolist()
        vuln_types = vuln_data["Security Vulnerability Type"].unique().tolist()

        # 為每個漏洞類型建立資料序列
        series_data = {}
        for vuln_type in vuln_types:
            vuln_subset = vuln_data[vuln_data["Security Vulnerability Type"] ==
                                    vuln_type]
            series_data[vuln_type] = {
                "attack_types": vuln_subset["Attack Type"].tolist(),
                "counts": vuln_subset["Count"].tolist(),
            }

        return jsonify({
            "attack_types": attack_types,
            "vuln_types": vuln_types,
            "series": series_data,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/yearly_trend")
def get_yearly_trend():
    """年度攻擊趨勢與財務損失"""
    try:
        df = df_global.copy()

        # 按年份統計事件數和財務損失
        yearly_stats = (df.groupby("Year").agg({
            "Country":
            "count",
            "Financial Loss (in Million $)":
            "sum"
        }).reset_index())
        yearly_stats.columns = ["Year", "Count", "Loss"]

        return jsonify({
            "years": yearly_stats["Year"].tolist(),
            "counts": yearly_stats["Count"].tolist(),
            "losses": yearly_stats["Loss"].tolist(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/statistics")
def get_statistics():
    """統計資料"""
    try:
        df = df_global.copy()

        stats = {
            "total_attacks":
            int(df.shape[0]),
            "unique_countries":
            int(df["Country"].nunique()),
            "attack_types":
            int(df["Attack Type"].nunique()),
            "date_range":
            f"{int(df['Year'].min())} ~ {int(df['Year'].max())}",
            "most_common_attack":
            (df["Attack Type"].mode()[0] if not df.empty else "N/A"),
            "most_targeted_port":
            (df["Target Industry"].mode()[0] if not df.empty else "N/A"),
        }

        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/defense_resolution")
def get_defense_resolution():
    """盒鬚圖：防禦方法與事件解決時間比較"""
    try:
        df = df_global.copy()

        # 使用正確的欄位名稱
        defense_col = "Defense Mechanism Used"
        resolution_col = "Incident Resolution Time (in Hours)"

        # 確保數據列存在
        if defense_col not in df.columns or resolution_col not in df.columns:
            return (
                jsonify({
                    "error": "Required columns not found",
                    "available_columns": list(df.columns),
                }),
                400,
            )

        # 移除空值
        df_clean = df.dropna(subset=[defense_col, resolution_col])

        if df_clean.empty:
            return jsonify({
                "defense_methods": [],
                "resolution_data": {},
                "statistics": {}
            })

        # 獲取所有防禦方法
        defense_methods = df_clean[defense_col].unique().tolist()

        # 為每種防禦方法準備盒鬚圖數據
        resolution_data = {}
        statistics = {}

        for method in defense_methods:
            method_data = df_clean[df_clean[defense_col] ==
                                   method][resolution_col]

            if len(method_data) > 0:
                resolution_data[method] = method_data.tolist()

                # 計算統計數據 - 確保針對每個方法單獨計算
                statistics[method] = {
                    "count": len(method_data),
                    "mean": float(method_data.mean()),
                    "median": float(method_data.median()),
                    "q1": float(method_data.quantile(0.25)),
                    "q3": float(method_data.quantile(0.75)),
                    "min": float(method_data.min()),  # 這應該是該方法的實際最小值
                    "max": float(method_data.max()),  # 這應該是該方法的實際最大值
                    "std": float(method_data.std()),
                }

        return jsonify({
            "defense_methods": defense_methods,
            "resolution_data": resolution_data,
            "statistics": statistics,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
