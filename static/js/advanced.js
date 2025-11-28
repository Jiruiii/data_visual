/**
 * 進階分析頁面 - Plotly.js 圖表
 * Advanced page - Heatmap diagram and Treemap
 */

/**
 * 載入 Heatmap 圖
 */
async function loadHeatmap() {
    const chartDiv = document.getElementById('heatmap-chart');
    try {
        chartDiv.classList.add('loading');
        chartDiv.innerHTML = '<div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>';

        const response = await fetch('/api/heatmap');
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        chartDiv.classList.remove('loading');
        chartDiv.innerHTML = '';

        // Create Heatmap
        const trace = {
            type: 'heatmap',
            x: data.attack_types,
            y: data.industries,
            z: data.heatmap_data,
            colorscale: 'RdBu',
            colorbar: {
                title: {
                    text: '平均損失<br>(百萬美元)',
                    side: 'right'
                },
                thickness: 20,
                len: 0.7,
                tickformat: ',.0f',
                ticksuffix: 'M'
            },
            hovertemplate: '<b>產業：%{y}</b><br>' +
                          '<b>攻擊類型：%{x}</b><br>' +
                          '平均財務損失: $%{z:,.2f}M<br>' +
                          '<extra></extra>',
            xgap: 2,
            ygap: 2
        };

        const layout = {
            title: {
                text: '各產業 × 攻擊類型的平均財務損失熱力圖',
                font: {
                    family: 'Microsoft JhengHei, Arial',
                    size: 18
                }
            },
            xaxis: {
                title: '攻擊類型',
                tickangle: -45,
                side: 'bottom',
                tickfont: { size: 11 }
            },
            yaxis: {
                title: '目標產業',
                side: 'left',
                tickfont: { size: 11 }
            },
            height: 700,
            font: {
                family: 'Microsoft JhengHei, Arial',
                size: 12
            },
            margin: {
                l: 150,
                r: 100,
                t: 100,
                b: 150
            }
        };

        Plotly.newPlot('heatmap-chart', [trace], layout, {
            responsive: true,
            displayModeBar: true
        });

        // Update statistics display
        updateHeatmapStatistics(data.statistics);

    } catch (error) {
        console.error('Error loading Heatmap:', error);
        chartDiv.classList.remove('loading');
        chartDiv.innerHTML = 
            '<div class="alert alert-danger">載入熱力圖失敗：' + error.message + '</div>';
    }
}

/**
 * 載入 Treemap 樹狀圖
 */
async function loadTreemap() {
    const chartDiv = document.getElementById("treemap-chart");
    try {
        const response = await fetch("/api/treemap");
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // 驗證資料
        console.log(data);

        // 檢查是否有 NaN 值
        const hasNaN = data.values.some(
            (v) => v === null || v === undefined || isNaN(v)
        );
        if (hasNaN) {
            throw new Error("資料中包含無效數值");
        }

        chartDiv.classList.remove("loading");
        chartDiv.innerHTML = "";

        const trace = {
            type: "treemap",
            labels: data.labels,
            parents: data.parents,
            values: data.values,
            branchvalues: "total", // 確保父節點值為子節點值之和
            textposition: "middle center",
            marker: {
                colors: data.values,
                colorscale: "Viridis",
                cmid: Math.max(...data.values) / 2,
                colorbar: {
                    title: "事件數",
                    thickness: 20,
                    len: 0.7,
                },
                line: {
                    width: 2,
                    color: "white",
                },
            },
            textinfo: "label+value+percent parent",
            texttemplate: "<b>%{label}</b><br>%{value}<br>%{percentParent:.1%}",
            textfont: {
                family: "Microsoft JhengHei, Arial",
                size: 12,
            },
            hovertemplate:
                "<b>%{label}</b><br>事件數: %{value:,.0f}<br>佔比: %{percentParent:.1%}<extra></extra>",
        };

        const layout = {
            title: {
                text: "目標產業與攻擊類型分布（樹狀圖）",
                font: { family: "Microsoft JhengHei, Arial", size: 16 },
            },
            font: {
                family: "Microsoft JhengHei, Arial",
                size: 11,
            },
            height: 600,
            margin: { t: 50, l: 25, r: 25, b: 25 },
        };

        Plotly.newPlot("treemap-chart", [trace], layout, {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            displaylogo: false
        });

        document.getElementById('treemap-chart').on('plotly_treemapclick', function(data) {
            console.log('Clicked:', data.points[0].label);
            console.log('Value:', data.points[0].value);
            console.log('Percent of parent:', data.points[0].percentParent);
        });
    } catch (error) {
        console.error("Error loading Treemap:", error);
        chartDiv.classList.remove("loading");
        chartDiv.innerHTML =
            '<div class="alert alert-danger">載入 Treemap 失敗：' + error.message + "</div>";
    }
}

// Update heatmap statistics display
function updateHeatmapStatistics(stats) {
    const statsDiv = document.getElementById('heatmap-stats');
    if (!statsDiv) return;

    statsDiv.innerHTML = `
        <div class="row">
            <div class="col-md-3">
                <div class="card text-center border-0 shadow-sm">
                    <div class="card-body">
                        <h6 class="text-muted">最高平均損失</h6>
                        <h5 class="text-danger">$${stats.max_loss.value.toFixed(1)}M</h5>
                        <small>${stats.max_loss.industry}<br>${stats.max_loss.attack}</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center border-0 shadow-sm">
                    <div class="card-body">
                        <h6 class="text-muted">最低平均損失</h6>
                        <h5 class="text-success">$${stats.min_loss.value.toFixed(1)}M</h5>
                        <small>${stats.min_loss.industry}<br>${stats.min_loss.attack}</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center border-0 shadow-sm">
                    <div class="card-body">
                        <h6 class="text-muted">總體平均損失</h6>
                        <h5 class="text-warning">$${stats.avg_loss_overall.toFixed(1)}M</h5>
                        <small>所有組合平均</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center border-0 shadow-sm">
                    <div class="card-body">
                        <h6 class="text-muted">組合總數</h6>
                        <h5 class="text-info">${stats.total_combinations}</h5>
                        <small>${stats.total_industries} 產業 × ${stats.total_attack_types} 攻擊</small>
                    </div>
                </div>
            </div>
        </div>
    `;
    statsDiv.style.display = 'block';
}

/**
 * 初始化進階分析頁面
 */
function initAdvancedPage() {
    loadHeatmap();
    loadTreemap();
}

// 頁面載入時初始化
document.addEventListener("DOMContentLoaded", initAdvancedPage);
