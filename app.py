from flask import Flask, render_template, jsonify, request
import pandas as pd
import plotly
import plotly.graph_objs as go
import plotly.express as px
import json
from datetime import datetime
import os
import urllib.request
import zipfile

# 載入 .env 檔案（如果存在）
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv()
        print("✓ 已載入 .env 環境變數")
except ImportError:
    pass  # 如果沒安裝 python-dotenv 也沒關係

app = Flask(__name__)

def download_kaggle_dataset():
    """嘗試從 Kaggle 下載資料集（需要 kaggle API）"""
    try:
        print("正在嘗試使用 Kaggle API 下載資料集...")
        
        # 方法1: 從環境變數讀取 (GitHub Secrets)
        kaggle_username = os.environ.get('KAGGLE_USERNAME')
        kaggle_key = os.environ.get('KAGGLE_KEY')
        
        if kaggle_username and kaggle_key:
            print("✓ 從環境變數讀取 Kaggle 憑證")
            os.environ['KAGGLE_USERNAME'] = kaggle_username
            os.environ['KAGGLE_KEY'] = kaggle_key
        # 方法2: 使用專案內的 kaggle.json
        elif os.path.exists('kaggle.json'):
            print("✓ 找到專案內的 kaggle.json")
            os.environ['KAGGLE_CONFIG_DIR'] = os.path.abspath('.')
        # 方法3: 使用系統的 kaggle.json
        else:
            print("• 嘗試使用系統的 Kaggle 設定")
        
        import kaggle
        
        # 下載資料集
        kaggle.api.dataset_download_files(
            'atharvasoundankar/global-cybersecurity-threats-2015-2024',
            path='data/',
            unzip=True
        )
        print("✓ 成功從 Kaggle 下載資料集")
        return True
    except ImportError:
        print("! 未安裝 kaggle 套件，請執行: pip install kaggle")
        return False
    except Exception as e:
        print(f"! 無法從 Kaggle 下載: {e}")
        print("\n請選擇以下任一方式設定 Kaggle 認證：")
        print("  1. 將 kaggle.json 放到專案根目錄")
        print("  2. 設定環境變數 KAGGLE_USERNAME 和 KAGGLE_KEY")
        print("  3. 將 kaggle.json 放到 ~/.kaggle/ 資料夾")
        return False

# 載入資料
def load_data():
    """載入網路安全威脅資料集"""
    data_path = 'data/cybersecurity_threats.csv'
    
    # 檢查資料檔案是否存在
    if not os.path.exists(data_path):
        print(f"找不到資料檔案: {data_path}")
        
        # 嘗試從 Kaggle 下載
        print("\n選項 1: 自動從 Kaggle 下載（需要 Kaggle API）")
        print("選項 2: 使用範例資料")
        print("\n正在嘗試自動下載...")
        
        if download_kaggle_dataset():
            # 下載成功，尋找 CSV 檔案
            data_dir = 'data'
            csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
            if csv_files:
                data_path = os.path.join(data_dir, csv_files[0])
                print(f"✓ 找到資料檔案: {data_path}")
            else:
                print("! 下載的資料中沒有找到 CSV 檔案")
                print("使用範例資料...")
                return create_sample_data()
        else:
            print("\n使用範例資料進行測試...")
            return create_sample_data()
    
    try:
        print(f"正在載入資料: {data_path}")
        df = pd.read_csv(data_path)
        print(f"✓ 成功載入 {len(df)} 筆資料")
        
        # 資料前處理
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df['Year'] = df['Timestamp'].dt.year
            df['Month'] = df['Timestamp'].dt.month
            df['Hour'] = df['Timestamp'].dt.hour
            df['Date'] = df['Timestamp'].dt.date
        
        return df
    except Exception as e:
        print(f"載入資料時發生錯誤: {e}")
        print("使用範例資料...")
        return create_sample_data()

def create_sample_data():
    """建立範例資料用於測試"""
    import numpy as np
    from datetime import timedelta
    
    np.random.seed(42)
    n_samples = 5000
    
    countries = ['USA', 'China', 'Russia', 'Brazil', 'India', 'Germany', 'UK', 'France', 'Japan', 'South Korea',
                 'Canada', 'Australia', 'Mexico', 'Spain', 'Italy', 'Netherlands', 'Turkey', 'Indonesia', 'Poland', 'Sweden']
    attack_types = ['DDoS', 'Port Scan', 'SQL Injection', 'Phishing', 'Malware', 'Ransomware', 'Brute Force', 'XSS']
    ports = [80, 443, 22, 21, 3389, 8080, 3306, 5432, 25, 53]
    
    base_date = datetime(2015, 1, 1)
    dates = [base_date + timedelta(days=int(x)) for x in np.random.randint(0, 3650, n_samples)]
    
    data = {
        'Timestamp': dates,
        'Source_Country': np.random.choice(countries, n_samples, p=[0.15, 0.12, 0.10, 0.08, 0.08, 0.05, 0.05, 0.04, 0.04, 0.04,
                                                                     0.03, 0.03, 0.03, 0.03, 0.03, 0.02, 0.02, 0.02, 0.02, 0.02]),
        'Target_Country': np.random.choice(countries, n_samples),
        'Source_IP': [f"{np.random.randint(1,255)}.{np.random.randint(1,255)}.{np.random.randint(1,255)}.{np.random.randint(1,255)}" 
                      for _ in range(n_samples)],
        'Target_IP': [f"{np.random.randint(1,255)}.{np.random.randint(1,255)}.{np.random.randint(1,255)}.{np.random.randint(1,255)}" 
                      for _ in range(n_samples)],
        'Attack_Type': np.random.choice(attack_types, n_samples, p=[0.25, 0.20, 0.15, 0.12, 0.10, 0.08, 0.06, 0.04]),
        'Port': np.random.choice(ports, n_samples),
        'Severity': np.random.choice(['Low', 'Medium', 'High', 'Critical'], n_samples, p=[0.2, 0.3, 0.35, 0.15]),
        'Attack_Duration_Seconds': np.random.randint(1, 3600, n_samples)
    }
    
    df = pd.DataFrame(data)
    df['Year'] = df['Timestamp'].dt.year
    df['Month'] = df['Timestamp'].dt.month
    df['Hour'] = df['Timestamp'].dt.hour
    df['Date'] = df['Timestamp'].dt.date
    
    # 儲存範例資料
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/cybersecurity_threats.csv', index=False)
    
    return df

# 全域變數儲存資料
df_global = load_data()

@app.route('/')
def index():
    """首頁"""
    return render_template('index.html')

@app.route('/overview')
def overview():
    """概覽頁面"""
    return render_template('overview.html')

@app.route('/map')
def map_view():
    """地圖視覺化頁面"""
    return render_template('map.html')

@app.route('/charts')
def charts():
    """圖表頁面"""
    return render_template('charts.html')

@app.route('/advanced')
def advanced():
    """進階圖表頁面"""
    return render_template('advanced.html')

@app.route('/api/map_data')
def get_map_data():
    """取得地圖資料 - 攻擊來源國與目標國"""
    try:
        df = df_global.copy()
        
        # 計算每個來源國家的攻擊次數
        source_counts = df['Source_Country'].value_counts().reset_index()
        source_counts.columns = ['Country', 'Count']
        
        # 建立地圖
        fig = px.choropleth(
            source_counts,
            locations='Country',
            locationmode='country names',
            color='Count',
            hover_name='Country',
            hover_data={'Count': True},
            color_continuous_scale='Reds',
            title='全球網路攻擊來源國分布圖 (2015-2024)'
        )
        
        fig.update_layout(
            geo=dict(
                showframe=False,
                showcoastlines=True,
                projection_type='natural earth'
            ),
            height=600,
            font=dict(family="Microsoft JhengHei, Arial", size=14)
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/top_ips')
def get_top_ips():
    """取得 TOP 10 攻擊來源 IP"""
    try:
        df = df_global.copy()
        
        # 計算 TOP 10 IP
        top_ips = df['Source_IP'].value_counts().head(10).reset_index()
        top_ips.columns = ['IP', 'Count']
        
        fig = go.Figure(data=[
            go.Bar(
                x=top_ips['Count'],
                y=top_ips['IP'],
                orientation='h',
                marker=dict(
                    color=top_ips['Count'],
                    colorscale='Viridis',
                    showscale=True
                ),
                text=top_ips['Count'],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title='TOP 10 攻擊來源 IP',
            xaxis_title='攻擊次數',
            yaxis_title='來源 IP',
            height=500,
            font=dict(family="Microsoft JhengHei, Arial", size=12),
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attack_types')
def get_attack_types():
    """取得攻擊類型圓餅圖"""
    try:
        df = df_global.copy()
        
        # 計算各種攻擊類型的比例
        attack_counts = df['Attack_Type'].value_counts().reset_index()
        attack_counts.columns = ['Attack_Type', 'Count']
        
        fig = go.Figure(data=[
            go.Pie(
                labels=attack_counts['Attack_Type'],
                values=attack_counts['Count'],
                hole=0.3,
                marker=dict(
                    colors=px.colors.qualitative.Set3
                ),
                textinfo='label+percent',
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title='不同攻擊類型佔比 (DDoS, Port Scan, SQL Injection...)',
            height=500,
            font=dict(family="Microsoft JhengHei, Arial", size=12)
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/time_series')
def get_time_series():
    """取得時間序列折線圖 - 每小時攻擊次數變化"""
    try:
        df = df_global.copy()
        
        # 按小時統計攻擊次數
        hourly_counts = df.groupby('Hour').size().reset_index(name='Count')
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=hourly_counts['Hour'],
            y=hourly_counts['Count'],
            mode='lines+markers',
            name='攻擊次數',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(255, 107, 107, 0.2)'
        ))
        
        fig.update_layout(
            title='24小時攻擊次數變化趨勢',
            xaxis_title='時間 (小時)',
            yaxis_title='攻擊次數',
            height=400,
            font=dict(family="Microsoft JhengHei, Arial", size=12),
            hovermode='x unified'
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sankey')
def get_sankey():
    """取得 Sankey 圖 - 來源國 -> 攻擊類型 -> 目標埠號"""
    try:
        df = df_global.copy()
        
        # 取前 10 個來源國、前 6 種攻擊類型、前 5 個埠號
        top_countries = df['Source_Country'].value_counts().head(10).index.tolist()
        top_attacks = df['Attack_Type'].value_counts().head(6).index.tolist()
        top_ports = df['Port'].value_counts().head(5).index.tolist()
        
        # 過濾資料
        df_filtered = df[
            (df['Source_Country'].isin(top_countries)) &
            (df['Attack_Type'].isin(top_attacks)) &
            (df['Port'].isin(top_ports))
        ]
        
        # 建立節點標籤
        all_nodes = top_countries + top_attacks + [f"Port {p}" for p in top_ports]
        node_dict = {node: idx for idx, node in enumerate(all_nodes)}
        
        # 建立連結 - 來源國 -> 攻擊類型
        link1 = df_filtered.groupby(['Source_Country', 'Attack_Type']).size().reset_index(name='value')
        link1 = link1[link1['value'] > 5]  # 過濾小數值
        
        # 建立連結 - 攻擊類型 -> 目標埠號
        link2 = df_filtered.groupby(['Attack_Type', 'Port']).size().reset_index(name='value')
        link2 = link2[link2['value'] > 5]
        link2['Port'] = 'Port ' + link2['Port'].astype(str)
        
        # 合併連結
        sources = link1['Source_Country'].map(node_dict).tolist() + link2['Attack_Type'].map(node_dict).tolist()
        targets = link1['Attack_Type'].map(node_dict).tolist() + link2['Port'].map(node_dict).tolist()
        values = link1['value'].tolist() + link2['value'].tolist()
        
        # 建立 Sankey 圖
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
                color=['#FF6B6B'] * len(top_countries) + 
                      ['#4ECDC4'] * len(top_attacks) + 
                      ['#95E1D3'] * len(top_ports)
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color='rgba(0,0,0,0.2)'
            )
        )])
        
        fig.update_layout(
            title='攻擊流向視覺化：來源國 → 攻擊類型 → 目標埠號',
            font=dict(family="Microsoft JhengHei, Arial", size=12),
            height=700
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/treemap')
def get_treemap():
    """取得樹狀圖 - 顯示不同目標埠號被攻擊的次數分布"""
    try:
        df = df_global.copy()
        
        # 統計每個埠號被攻擊的次數
        port_counts = df.groupby(['Port', 'Attack_Type']).size().reset_index(name='Count')
        port_counts = port_counts[port_counts['Count'] > 10]  # 過濾小數值
        port_counts['Port_Label'] = 'Port ' + port_counts['Port'].astype(str)
        
        fig = px.treemap(
            port_counts,
            path=['Port_Label', 'Attack_Type'],
            values='Count',
            color='Count',
            color_continuous_scale='RdYlGn_r',
            title='目標埠號被攻擊次數分布 (樹狀圖)'
        )
        
        fig.update_layout(
            height=600,
            font=dict(family="Microsoft JhengHei, Arial", size=12)
        )
        
        fig.update_traces(
            textinfo="label+value+percent parent",
            hovertemplate='<b>%{label}</b><br>攻擊次數: %{value}<br>佔比: %{percentParent}<extra></extra>'
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/severity_by_type')
def get_severity_by_type():
    """取得攻擊嚴重程度分析"""
    try:
        df = df_global.copy()
        
        # 統計每種攻擊類型的嚴重程度分布
        severity_data = df.groupby(['Attack_Type', 'Severity']).size().reset_index(name='Count')
        
        fig = px.bar(
            severity_data,
            x='Attack_Type',
            y='Count',
            color='Severity',
            color_discrete_map={
                'Low': '#90EE90',
                'Medium': '#FFD700',
                'High': '#FF8C00',
                'Critical': '#FF0000'
            },
            title='各攻擊類型的嚴重程度分布',
            barmode='stack'
        )
        
        fig.update_layout(
            xaxis_title='攻擊類型',
            yaxis_title='攻擊次數',
            height=500,
            font=dict(family="Microsoft JhengHei, Arial", size=12),
            legend_title='嚴重程度'
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/yearly_trend')
def get_yearly_trend():
    """取得年度趨勢"""
    try:
        df = df_global.copy()
        
        # 按年份統計
        yearly_data = df.groupby('Year').size().reset_index(name='Count')
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=yearly_data['Year'],
            y=yearly_data['Count'],
            mode='lines+markers',
            name='總攻擊次數',
            line=dict(color='#667EEA', width=4),
            marker=dict(size=10, symbol='diamond')
        ))
        
        fig.update_layout(
            title='2015-2024 年度網路攻擊趨勢',
            xaxis_title='年份',
            yaxis_title='攻擊次數',
            height=400,
            font=dict(family="Microsoft JhengHei, Arial", size=12),
            hovermode='x unified'
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """取得統計資料"""
    try:
        df = df_global.copy()
        
        stats = {
            'total_attacks': int(df.shape[0]),
            'unique_source_ips': int(df['Source_IP'].nunique()),
            'unique_countries': int(df['Source_Country'].nunique()),
            'attack_types': int(df['Attack_Type'].nunique()),
            'date_range': f"{df['Timestamp'].min().strftime('%Y-%m-%d')} ~ {df['Timestamp'].max().strftime('%Y-%m-%d')}",
            'most_common_attack': df['Attack_Type'].mode()[0] if not df.empty else 'N/A',
            'most_targeted_port': int(df['Port'].mode()[0]) if not df.empty else 0
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
