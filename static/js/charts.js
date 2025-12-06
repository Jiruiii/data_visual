/**
 * 基本圖表頁面 - Plotly.js 圖表
 * Charts page - Bar, Pie, Box plots
 */

let currentIndustryChart = 'count';

/**
 * 切換產業圖表類型
 * @param {string} type - 圖表類型 (count/loss)
 */
function switchIndustryChart(type) {
    currentIndustryChart = type;

    // Update button states
    document.getElementById('attack-count-btn').className =
        type === 'count' ? 'btn btn-primary active' : 'btn btn-outline-primary';
    document.getElementById('financial-loss-btn').className =
        type === 'loss' ? 'btn btn-primary active' : 'btn btn-outline-primary';

    // Update insights
    document.getElementById('count-insights').style.display = type === 'count' ? 'block' : 'none';
    document.getElementById('loss-insights').style.display = type === 'loss' ? 'block' : 'none';

    // Reload chart
    loadIndustryChart();
}

/**
 * 載入產業分析橫向長條圖
 */
async function loadIndustryChart() {
    const chartDiv = document.getElementById('industry-chart');
    try {
        chartDiv.classList.add('loading');
        chartDiv.innerHTML = '<div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>';

        const response = await fetch(`/api/industry_analysis?type=${currentIndustryChart}`);
        const data = await response.json();
        chartDiv.classList.remove('loading');
        chartDiv.innerHTML = '';

        // Create horizontal bar chart
        const trace = {
            type: 'bar',
            x: data.values,
            y: data.labels,
            orientation: 'h',
            marker: {
                color: data.values,
                colorscale: currentIndustryChart === 'count' ?
                    [
                        [0, '#E3F2FD'],
                        [0.5, '#2196F3'],
                        [1, '#0D47A1']
                    ] :
                    [
                        [0, '#FFEBEE'],
                        [0.5, '#F44336'],
                        [1, '#B71C1C']
                    ],
                showscale: true,
                colorbar: {
                    title: currentIndustryChart === 'count' ? '攻擊次數' : '財務損失 (百萬美元)',
                    titlefont: { family: 'Microsoft JhengHei, Arial' }
                }
            },
            text: data.values.map(v => currentIndustryChart === 'count' ?
                v.toLocaleString() : `$${v.toFixed(1)}M`),
            textposition: 'auto',
            hovertemplate: `<b>%{y}</b><br>${currentIndustryChart === 'count' ? '攻擊次數' : '財務損失'}: %{x${currentIndustryChart === 'count' ? ':,' : ':.1f'}}<extra></extra>`
        };

        const layout = {
            title: {
                text: `產業類型${currentIndustryChart === 'count' ? '攻擊次數' : '財務損失'}分析`,
                font: { family: 'Microsoft JhengHei, Arial', size: 16 },
                x: 0.5
            },
            xaxis: {
                title: {
                    text: currentIndustryChart === 'count' ? '攻擊次數' : '財務損失 (百萬美元)',
                    font: { family: 'Microsoft JhengHei, Arial', size: 14 }
                },
                tickfont: { size: 12 }
            },
            yaxis: {
                title: {
                    text: '產業類型',
                    font: { family: 'Microsoft JhengHei, Arial', size: 14 },
                    standoff: 25
                },
                font: { family: 'Microsoft JhengHei, Arial' },
                categoryorder: 'total ascending',
                tickfont: {
                    size: 11,
                    family: 'Microsoft JhengHei, Arial'
                },
                automargin: true
            },
            height: 500,
            font: { family: 'Microsoft JhengHei, Arial', size: 12 },
            hovermode: 'closest',
            margin: {
                l: 200,
                r: 80,
                t: 100,
                b: 60
            },
            showlegend: false
        };

        Plotly.newPlot('industry-chart', [trace], layout, { responsive: true, displayModeBar: true });
    } catch (error) {
        console.error('Error loading industry chart:', error);
        chartDiv.classList.remove('loading');
        chartDiv.innerHTML = '<div class="alert alert-danger">載入圖表失敗</div>';
    }
}

/**
 * 載入攻擊類型圓餅圖
 */
async function loadAttackTypes() {
    const chartDiv = document.getElementById('attack-types-chart');
    try {
        const response = await fetch('/api/attack_types');
        const data = await response.json();
        chartDiv.classList.remove('loading');
        chartDiv.innerHTML = '';

        // Create pie chart
        const trace = {
            type: 'pie',
            labels: data.labels,
            values: data.values,
            hole: 0.3,
            marker: {
                colors: [
                    '#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3',
                    '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd'
                ]
            },
            textinfo: 'label+percent',
            textposition: 'auto',
            insidetextorientation: 'horizontal',
            textfont: {
                size: 11
            },
            hovertemplate: '<b>%{label}</b><br>數量: %{value}<br>佔比: %{percent}<extra></extra>'
        };

        const layout = {
            title: {
                text: '不同攻擊類型佔比分析',
                font: { family: 'Microsoft JhengHei, Arial', size: 16 }
            },
            height: 550,
            font: { family: 'Microsoft JhengHei, Arial', size: 12 },
            // margin: {
            //     l: 100,
            //     r: 100,
            //     t: 80,
            //     b: 80
            // }
        };

        Plotly.newPlot('attack-types-chart', [trace], layout, { responsive: true, displayModeBar: true });
    } catch (error) {
        console.error('Error loading attack types:', error);
        chartDiv.classList.remove('loading');
        chartDiv.innerHTML = '<div class="alert alert-danger">載入圖表失敗</div>';
    }
}

/**
 * 載入防禦方法與解決時間盒鬚圖
 */
async function loadDefenseResolution() {
    const chartDiv = document.getElementById('defense-resolution-chart');
    try {
        const response = await fetch('/api/defense_resolution');
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        chartDiv.classList.remove('loading');
        chartDiv.innerHTML = '';

        // 準備盒鬚圖數據
        const traces = [];
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'];

        data.defense_methods.forEach((method, index) => {
            if (data.resolution_data[method] && data.resolution_data[method].length > 0) {
                traces.push({
                    type: 'box',
                    y: data.resolution_data[method],
                    name: method,
                    boxpoints: 'outliers',
                    marker: {
                        color: colors[index % colors.length],
                        outliercolor: 'rgba(219, 64, 82, 0.6)',
                        line: {
                            outliercolor: 'rgba(219, 64, 82, 0.6)',
                            outlierwidth: 2
                        }
                    },
                    line: {
                        color: colors[index % colors.length]
                    }
                });
            }
        });

        const layout = {
            title: {
                text: '防禦方法與事件解決時間比較',
                font: { family: 'Microsoft JhengHei, Arial', size: 16 }
            },
            xaxis: {
                title: {
                    text: '防禦方法',
                    font: { family: 'Microsoft JhengHei, Arial', size: 14 }
                },
                tickangle: -45,
                automargin: true
            },
            yaxis: {
                title: {
                    text: '事件解決時間 (小時)',
                    font: { family: 'Microsoft JhengHei, Arial', size: 14 }
                }
            },
            height: 500,
            font: { family: 'Microsoft JhengHei, Arial', size: 12 },
            hovermode: 'closest',
            margin: {
                l: 80,
                r: 50,
                t: 100,
                b: 120
            }
        };

        Plotly.newPlot('defense-resolution-chart', traces, layout, {
            responsive: true,
            displayModeBar: true
        });

        // 更新統計表格
        updateDefenseStatsTable(data.statistics);

    } catch (error) {
        console.error('Error loading defense resolution chart:', error);
        chartDiv.classList.remove('loading');
        chartDiv.innerHTML = '<div class="alert alert-danger">載入圖表失敗: ' + error.message + '</div>';
    }
}

/**
 * 更新防禦統計表格
 * @param {Object} statistics - 統計數據
 */
function updateDefenseStatsTable(statistics) {
    const tbody = document.querySelector('#defense-stats-table tbody');
    tbody.innerHTML = '';

    Object.keys(statistics).forEach(method => {
        const stats = statistics[method];
        const row = tbody.insertRow();

        row.innerHTML = `
            <td><strong>${method}</strong></td>
            <td>${stats.count}</td>
            <td>${stats.mean.toFixed(1)}h</td>
            <td>${stats.median.toFixed(1)}h</td>
            <td>${stats.std.toFixed(1)}h</td>
            <td>${stats.min.toFixed(1)}h</td>
            <td>${stats.max.toFixed(1)}h</td>
        `;
    });
}

/**
 * 初始化圖表頁面
 */
function initChartsPage() {
    loadIndustryChart();
    loadAttackTypes();
    loadDefenseResolution();
}

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', initChartsPage);
