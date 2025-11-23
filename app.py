from flask import Flask, render_template, jsonify, request
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import json
import os

# 載入 .env 檔案
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv()
        print("✓ 已載入 .env 環境變數")
except ImportError:
    pass

app = Flask(__name__)

def download_kaggle_dataset():
    """從 Kaggle 下載資料集"""
    try:
        print("正在嘗試使用 Kaggle API 下載資料集...")
        
        kaggle_username = os.environ.get('KAGGLE_USERNAME')
        kaggle_key = os.environ.get('KAGGLE_KEY')
        
        if kaggle_username and kaggle_key:
            print("✓ 從環境變數讀取 Kaggle 憑證")
            os.environ['KAGGLE_USERNAME'] = kaggle_username
            os.environ['KAGGLE_KEY'] = kaggle_key
        elif os.path.exists('kaggle.json'):
            print("✓ 找到專案內的 kaggle.json")
            os.environ['KAGGLE_CONFIG_DIR'] = os.path.abspath('.')
        
        import kaggle
        kaggle.api.dataset_download_files(
            'atharvasoundankar/global-cybersecurity-threats-2015-2024',
            path='data/',
            unzip=True
        )
        print("✓ 成功從 Kaggle 下載資料集")
        return True
    except Exception as e:
        print(f"! 無法從 Kaggle 下載: {e}")
        return False

def load_data():
    """載入網路安全威脅資料集"""
    if download_kaggle_dataset():
        data_dir = 'data'
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if csv_files:
            data_path = os.path.join(data_dir, csv_files[0])
            print(f"✓ 找到資料檔案: {data_path}")
            
            df = pd.read_csv(data_path)
            print(f"✓ 成功載入 {len(df)} 筆資料")
            print(f"資料欄位: {list(df.columns)}")
            
            # 資料前處理
            if 'Year' in df.columns:
                df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
            
            return df
    return pd.DataFrame()

# 載入資料
df_global = load_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/overview')
def overview():
    return render_template('overview.html')

@app.route('/map')
def map_view():
    return render_template('map.html')

@app.route('/charts')
def charts():
    return render_template('charts.html')

@app.route('/advanced')
def advanced():
    return render_template('advanced.html')

@app.route('/api/map_data')
def get_map_data():
    """地圖：各國網路攻擊事件數量"""
    try:
        df = df_global.copy()
        country_counts = df['Country'].value_counts().reset_index()
        country_counts.columns = ['Country', 'Count']
        
        fig = px.choropleth(
            country_counts,
            locations='Country',
            locationmode='country names',
            color='Count',
            hover_name='Country',
            hover_data={'Count': True},
            color_continuous_scale='Reds',
            title='全球網路安全事件分布圖 (2015-2024)'
        )
        
        fig.update_layout(
            geo=dict(showframe=False, showcoastlines=True, projection_type='natural earth'),
            height=600,
            font=dict(family="Microsoft JhengHei, Arial", size=14)
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/countries')
def get_countries():
    """取得所有可用的國家列表"""
    try:
        df = df_global.copy()
        countries = sorted(df['Country'].unique().tolist())
        return jsonify({'countries': countries})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/top_ips')
def get_top_ips():
    """長條圖：TOP N 受影響使用者最多的事件（支援國家篩選）"""
    try:
        df = df_global.copy()
        
        country = request.args.get('country', 'all')
        top_n = int(request.args.get('top_n', 10))
        
        if country != 'all':
            df = df[df['Country'] == country]
        
        if df.empty:
            return jsonify({
                'data': [],
                'layout': {},
                'statistics': {
                    'total_events': 0,
                    'total_users': 0,
                    'avg_impact': 0
                }
            })
        
        top_incidents = df.nlargest(top_n, 'Number of Affected Users')[
            ['Country', 'Attack Type', 'Number of Affected Users']
        ]
        top_incidents['Label'] = top_incidents['Country'] + ' - ' + top_incidents['Attack Type']
        
        statistics = {
            'total_events': len(df),
            'total_users': int(df['Number of Affected Users'].sum()),
            'avg_impact': float(df['Number of Affected Users'].mean())
        }
        
        fig = go.Figure(data=[
            go.Bar(
                x=top_incidents['Number of Affected Users'],
                y=top_incidents['Label'],
                orientation='h',
                marker=dict(
                    color=top_incidents['Number of Affected Users'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title='影響人數')
                ),
                text=top_incidents['Number of Affected Users'].apply(lambda x: f'{x:,.0f}'),
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>受影響使用者: %{x:,.0f}<extra></extra>'
            )
        ])
        
        title = f'TOP {top_n} 受影響使用者最多的網路攻擊事件'
        if country != 'all':
            title = f'{country} - {title}'
        
        fig.update_layout(
            title=title,
            xaxis_title='受影響使用者數量',
            yaxis_title='國家 - 攻擊類型',
            height=500,
            font=dict(family="Microsoft JhengHei, Arial", size=12),
            yaxis={'categoryorder': 'total ascending'},
            hovermode='closest'
        )
        
        return jsonify({
            'data': json.loads(fig.to_json())['data'],
            'layout': json.loads(fig.to_json())['layout'],
            'statistics': statistics
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/time_series')
def get_time_series():
    """折線圖：年度攻擊趨勢（支援單一國家或多國比較，包含財務損失）"""
    try:
        df = df_global.copy()
        
        country = request.args.get('country', 'all')
        countries_param = request.args.get('countries', '')
        mode = request.args.get('mode', 'single')
        
        fig = go.Figure()
        
        if mode == 'compare' and countries_param:
            # 多國比較模式
            countries = [c.strip() for c in countries_param.split(',') if c.strip()]
            
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
            
            for idx, country_name in enumerate(countries[:5]):
                country_df = df[df['Country'] == country_name]
                if not country_df.empty:
                    yearly_counts = country_df.groupby('Year').size().reset_index(name='Count')
                    
                    fig.add_trace(go.Scatter(
                        x=yearly_counts['Year'],
                        y=yearly_counts['Count'],
                        mode='lines+markers',
                        name=country_name,
                        line=dict(color=colors[idx % len(colors)], width=3),
                        marker=dict(size=8),
                        hovertemplate=f'<b>{country_name}</b><br>年份: %{{x}}<br>攻擊次數: %{{y:,.0f}}<extra></extra>'
                    ))
            
            title = f'{len(countries)} 個國家年度攻擊趨勢比較 (2015-2024)'
            
            fig.update_layout(
                title=title,
                xaxis_title='年份',
                yaxis_title='攻擊事件數量',
                height=500,
                font=dict(family="Microsoft JhengHei, Arial", size=12),
                hovermode='x unified',
                legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'),
                xaxis=dict(tickmode='linear', dtick=1)
            )
            
            return jsonify(json.loads(fig.to_json()))
            
        else:
            # 單一國家或全球模式（加上財務損失）
            if country != 'all':
                df = df[df['Country'] == country]
            
            if df.empty:
                return jsonify({'data': [], 'layout': {}, 'statistics': {}})
            
            # 計算每年的攻擊次數和財務損失
            yearly_stats = df.groupby('Year').agg({
                'Country': 'count',  # 攻擊次數
                'Financial Loss (in Million $)': 'sum'  # 財務損失總和
            }).reset_index()
            yearly_stats.columns = ['Year', 'Count', 'Loss']
            
            # 計算統計數據
            total = yearly_stats['Count'].sum()
            average = yearly_stats['Count'].mean()
            total_loss = yearly_stats['Loss'].sum()
            avg_loss = yearly_stats['Loss'].mean()
            
            # 計算趨勢（首尾年份增長率）
            if len(yearly_stats) >= 2:
                first_year_count = yearly_stats.iloc[0]['Count']
                last_year_count = yearly_stats.iloc[-1]['Count']
                if first_year_count > 0:
                    trend = ((last_year_count - first_year_count) / first_year_count) * 100
                else:
                    trend = 0
                
                # 財務損失趨勢
                first_year_loss = yearly_stats.iloc[0]['Loss']
                last_year_loss = yearly_stats.iloc[-1]['Loss']
                if first_year_loss > 0:
                    loss_trend = ((last_year_loss - first_year_loss) / first_year_loss) * 100
                else:
                    loss_trend = 0
            else:
                trend = 0
                loss_trend = 0
            
            statistics = {
                'total': int(total),
                'average': float(average),
                'trend': float(trend),
                'total_loss': float(total_loss),
                'avg_loss': float(avg_loss),
                'loss_trend': float(loss_trend)
            }
            
            # 添加攻擊次數折線（左 Y 軸）
            fig.add_trace(go.Scatter(
                x=yearly_stats['Year'],
                y=yearly_stats['Count'],
                mode='lines+markers',
                name='攻擊事件數',
                line=dict(color='#FF6B6B', width=4),
                marker=dict(size=10),
                fill='tozeroy',
                fillcolor='rgba(255, 107, 107, 0.2)',
                hovertemplate='<b>%{x}年</b><br>攻擊次數: %{y:,.0f}<extra></extra>',
                yaxis='y'
            ))
            
            # 添加財務損失折線（右 Y 軸）
            fig.add_trace(go.Scatter(
                x=yearly_stats['Year'],
                y=yearly_stats['Loss'],
                mode='lines+markers',
                name='財務損失 (百萬美元)',
                line=dict(color='#4ECDC4', width=4, dash='dash'),
                marker=dict(size=10, symbol='diamond'),
                hovertemplate='<b>%{x}年</b><br>財務損失: $%{y:,.2f}M<extra></extra>',
                yaxis='y2'
            ))
            
            title = '2015-2024 年度網路攻擊趨勢與財務損失'
            if country != 'all':
                title = f'{country} - {title}'
            
            fig.update_layout(
                title=title,
                xaxis_title='年份',
                yaxis=dict(
                    title='攻擊事件數量',
                    titlefont=dict(color='#FF6B6B'),
                    tickfont=dict(color='#FF6B6B')
                ),
                yaxis2=dict(
                    title='財務損失（百萬美元）',
                    titlefont=dict(color='#4ECDC4'),
                    tickfont=dict(color='#4ECDC4'),
                    overlaying='y',
                    side='right'
                ),
                height=500,
                font=dict(family="Microsoft JhengHei, Arial", size=12),
                hovermode='x unified',
                legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'),
                xaxis=dict(
                    tickmode='linear',
                    tick0=yearly_stats['Year'].min(),
                    dtick=1
                )
            )
            
            return jsonify({
                'data': json.loads(fig.to_json())['data'],
                'layout': json.loads(fig.to_json())['layout'],
                'statistics': statistics
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attack_types')
def get_attack_types():
    """圓餅圖：攻擊類型分布"""
    try:
        df = df_global.copy()
        attack_counts = df['Attack Type'].value_counts().reset_index()
        attack_counts.columns = ['Attack_Type', 'Count']
        
        fig = go.Figure(data=[
            go.Pie(
                labels=attack_counts['Attack_Type'],
                values=attack_counts['Count'],
                hole=0.3,
                marker=dict(colors=px.colors.qualitative.Set3),
                textinfo='label+percent',
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title='不同攻擊類型佔比分析',
            height=500,
            font=dict(family="Microsoft JhengHei, Arial", size=12)
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sankey')
def get_sankey():
    """Sankey 圖：國家 → 攻擊類型 → 目標產業"""
    try:
        df = df_global.copy()
        
        # 取前 10 國家、前 6 攻擊類型、前 8 目標產業
        top_countries = df['Country'].value_counts().head(10).index.tolist()
        top_attacks = df['Attack Type'].value_counts().head(6).index.tolist()
        top_industries = df['Target Industry'].value_counts().head(8).index.tolist()
        
        df_filtered = df[
            (df['Country'].isin(top_countries)) &
            (df['Attack Type'].isin(top_attacks)) &
            (df['Target Industry'].isin(top_industries))
        ]
        
        # 建立節點
        all_nodes = top_countries + top_attacks + top_industries
        node_dict = {node: idx for idx, node in enumerate(all_nodes)}
        
        # 連結 1: 國家 → 攻擊類型
        link1 = df_filtered.groupby(['Country', 'Attack Type']).size().reset_index(name='value')
        link1 = link1[link1['value'] > 2]
        
        # 連結 2: 攻擊類型 → 目標產業
        link2 = df_filtered.groupby(['Attack Type', 'Target Industry']).size().reset_index(name='value')
        link2 = link2[link2['value'] > 2]
        
        sources = link1['Country'].map(node_dict).tolist() + link2['Attack Type'].map(node_dict).tolist()
        targets = link1['Attack Type'].map(node_dict).tolist() + link2['Target Industry'].map(node_dict).tolist()
        values = link1['value'].tolist() + link2['value'].tolist()
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
                color=['#FF6B6B'] * len(top_countries) + 
                      ['#4ECDC4'] * len(top_attacks) + 
                      ['#95E1D3'] * len(top_industries)
            ),
            link=dict(source=sources, target=targets, value=values, color='rgba(0,0,0,0.2)')
        )])
        
        fig.update_layout(
            title='攻擊流向：國家 → 攻擊類型 → 目標產業',
            font=dict(family="Microsoft JhengHei, Arial", size=12),
            height=700
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/treemap')
def get_treemap():
    """Treemap：目標產業與攻擊類型分布"""
    try:
        df = df_global.copy()
        
        # 統計目標產業與攻擊類型
        industry_attack = df.groupby(['Target Industry', 'Attack Type']).size().reset_index(name='Count')
        industry_attack = industry_attack[industry_attack['Count'] > 5]
        
        fig = px.treemap(
            industry_attack,
            path=['Target Industry', 'Attack Type'],
            values='Count',
            color='Count',
            color_continuous_scale='RdYlGn_r',
            title='目標產業與攻擊類型分布（樹狀圖）'
        )
        
        fig.update_layout(
            height=600,
            font=dict(family="Microsoft JhengHei, Arial", size=12)
        )
        
        fig.update_traces(
            textinfo="label+value+percent parent",
            hovertemplate='<b>%{label}</b><br>事件數: %{value}<br>佔比: %{percentParent}<extra></extra>'
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/severity_by_type')
def get_severity_by_type():
    """攻擊類型與安全漏洞分析"""
    try:
        df = df_global.copy()
        
        # 統計攻擊類型與安全漏洞類型
        vuln_data = df.groupby(['Attack Type', 'Security Vulnerability Type']).size().reset_index(name='Count')
        vuln_data = vuln_data.nlargest(30, 'Count')
        
        fig = px.bar(
            vuln_data,
            x='Attack Type',
            y='Count',
            color='Security Vulnerability Type',
            title='各攻擊類型的安全漏洞分布',
            barmode='stack'
        )
        
        fig.update_layout(
            xaxis_title='攻擊類型',
            yaxis_title='事件數量',
            height=500,
            font=dict(family="Microsoft JhengHei, Arial", size=12),
            legend_title='安全漏洞類型'
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/yearly_trend')
def get_yearly_trend():
    """年度攻擊趨勢與財務損失"""
    try:
        df = df_global.copy()
        
        # 按年份統計事件數和財務損失
        yearly_stats = df.groupby('Year').agg({
            'Country': 'count',
            'Financial Loss (in Million $)': 'sum'
        }).reset_index()
        yearly_stats.columns = ['Year', 'Count', 'Loss']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=yearly_stats['Year'],
            y=yearly_stats['Count'],
            mode='lines+markers',
            name='攻擊事件數',
            line=dict(color='#667EEA', width=4),
            marker=dict(size=10),
            yaxis='y'
        ))
        
        fig.add_trace(go.Scatter(
            x=yearly_stats['Year'],
            y=yearly_stats['Loss'],
            mode='lines+markers',
            name='財務損失 (百萬美元)',
            line=dict(color='#FF6B6B', width=4, dash='dash'),
            marker=dict(size=10, symbol='diamond'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='2015-2024 年度網路攻擊趨勢與財務損失',
            xaxis_title='年份',
            yaxis_title='攻擊事件數量',
            yaxis2=dict(title='財務損失（百萬美元）', overlaying='y', side='right'),
            height=400,
            font=dict(family="Microsoft JhengHei, Arial", size=12),
            hovermode='x unified',
            legend=dict(x=0.01, y=0.99)
        )
        
        return jsonify(json.loads(fig.to_json()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """統計資料"""
    try:
        df = df_global.copy()
        
        stats = {
            'total_attacks': int(df.shape[0]),
            'unique_source_ips': int(df['Country'].nunique()),
            'unique_countries': int(df['Country'].nunique()),
            'attack_types': int(df['Attack Type'].nunique()),
            'date_range': f"{int(df['Year'].min())} ~ {int(df['Year'].max())}",
            'most_common_attack': df['Attack Type'].mode()[0] if not df.empty else 'N/A',
            'most_targeted_port': df['Target Industry'].mode()[0] if not df.empty else 'N/A'
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
