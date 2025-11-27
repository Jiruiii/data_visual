/**
 * 資料概覽頁面 - Plotly.js 圖表
 * Overview page charts
 */

let availableCountries = [];
let currentTimeSeriesCountry = "all";
let currentChartMode = "single";

/**
 * 載入可用國家列表
 */
async function loadCountries() {
    try {
        const response = await fetch("/api/countries");
        const data = await response.json();
        availableCountries = data.countries || [];

        // Populate country select for time series (single)
        const timeseriesCountrySelect = document.getElementById("timeseries-country-select");
        availableCountries.forEach((country) => {
            const option = document.createElement("option");
            option.value = country;
            option.textContent = country;
            timeseriesCountrySelect.appendChild(option);
        });

        // Populate country select for time series (multi)
        const timeseriesMultiSelect = document.getElementById("timeseries-multi-country");
        availableCountries.forEach((country) => {
            const option = document.createElement("option");
            option.value = country;
            option.textContent = country;
            timeseriesMultiSelect.appendChild(option);
        });
    } catch (error) {
        console.error("Error loading countries:", error);
    }
}

/**
 * 載入時間序列折線圖
 * @param {string} country - 國家篩選
 * @param {Array} countries - 多國比較
 * @param {string} mode - 模式 (single/compare)
 */
async function loadTimeSeries(country = "all", countries = [], mode = "single") {
    const chartDiv = document.getElementById("time-series-chart");
    const statsPanel = document.getElementById("timeseries-stats-panel");

    try {
        chartDiv.classList.add("loading");
        chartDiv.innerHTML = '<div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>';

        const params = new URLSearchParams();

        if (mode === "compare" && countries.length > 0) {
            params.append("countries", countries.join(","));
            params.append("mode", "compare");
        } else if (country !== "all") {
            params.append("country", country);
        }

        const response = await fetch(`/api/time_series?${params.toString()}`);
        const data = await response.json();

        chartDiv.classList.remove("loading");
        chartDiv.innerHTML = "";

        let traces = [];
        let layout = {};

        if (data.mode === 'compare') {
            // 多國比較模式
            const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'];

            data.series.forEach((series, idx) => {
                traces.push({
                    type: 'scatter',
                    mode: 'lines+markers',
                    x: series.years,
                    y: series.counts,
                    name: series.country,
                    line: {
                        color: colors[idx % colors.length],
                        width: 3
                    },
                    marker: { size: 8 },
                    hovertemplate: `<b>${series.country}</b><br>年份: %{x}<br>攻擊次數: %{y:,}<extra></extra>`
                });
            });

            layout = {
                title: {
                    text: `${data.series.length} 個國家年度攻擊趨勢比較 (2015-2024)`,
                    font: { family: 'Microsoft JhengHei, Arial', size: 16 }
                },
                xaxis: {
                    title: '年份',
                    font: { family: 'Microsoft JhengHei, Arial' },
                    tickmode: 'linear',
                    dtick: 1
                },
                yaxis: {
                    title: '攻擊事件數量',
                    font: { family: 'Microsoft JhengHei, Arial' }
                },
                height: 500,
                font: { family: 'Microsoft JhengHei, Arial', size: 12 },
                hovermode: 'x unified',
                legend: {
                    x: 0.01,
                    y: 0.99,
                    bgcolor: 'rgba(255,255,255,0.8)'
                }
            };

            statsPanel.style.display = 'none';

        } else {
            // 單一國家模式（含財務損失）
            traces = [
                {
                    type: 'scatter',
                    mode: 'lines+markers',
                    x: data.years,
                    y: data.counts,
                    name: '攻擊事件數',
                    line: { color: '#FF6B6B', width: 4 },
                    marker: { size: 10 },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(255, 107, 107, 0.2)',
                    hovertemplate: '<b>%{x}年</b><br>攻擊次數: %{y:,}<extra></extra>',
                    yaxis: 'y'
                },
                {
                    type: 'scatter',
                    mode: 'lines+markers',
                    x: data.years,
                    y: data.losses,
                    name: '財務損失 (百萬美元)',
                    line: { color: '#4ECDC4', width: 4, dash: 'dash' },
                    marker: { size: 10, symbol: 'diamond' },
                    hovertemplate: '<b>%{x}年</b><br>財務損失: $%{y:,.2f}M<extra></extra>',
                    yaxis: 'y2'
                }
            ];

            const title = data.country === 'all'
                ? '2015-2024 年度網路攻擊趨勢與財務損失'
                : `${data.country} - 2015-2024 年度網路攻擊趨勢與財務損失`;

            layout = {
                title: {
                    text: title,
                    font: { family: 'Microsoft JhengHei, Arial', size: 16 }
                },
                xaxis: {
                    title: '年份',
                    font: { family: 'Microsoft JhengHei, Arial' },
                    tickmode: 'linear',
                    dtick: 1
                },
                yaxis: {
                    title: '攻擊事件數量',
                    titlefont: { color: '#FF6B6B' },
                    tickfont: { color: '#FF6B6B' }
                },
                yaxis2: {
                    title: '財務損失（百萬美元）',
                    titlefont: { color: '#4ECDC4' },
                    tickfont: { color: '#4ECDC4' },
                    overlaying: 'y',
                    side: 'right'
                },
                height: 500,
                font: { family: 'Microsoft JhengHei, Arial', size: 12 },
                hovermode: 'x unified',
                legend: {
                    x: 0.01,
                    y: 0.99,
                    bgcolor: 'rgba(255,255,255,0.8)'
                }
            };

            if (data.statistics) {
                updateTimeSeriesStatistics(data.statistics, data.country);
                statsPanel.style.display = 'flex';
            }
        }

        Plotly.newPlot("time-series-chart", traces, layout, {
            responsive: true,
            displayModeBar: true
        });

        updateTimeSeriesDescription(country, countries, mode);

    } catch (error) {
        console.error("Error loading time series:", error);
        chartDiv.classList.remove("loading");
        chartDiv.innerHTML = '<div class="alert alert-danger">載入圖表失敗：' + error.message + "</div>";
    }
}

/**
 * 更新時間序列描述文字
 */
function updateTimeSeriesDescription(country, countries, mode) {
    const descSpan = document.getElementById("timeseries-description");
    if (mode === "compare" && countries.length > 0) {
        descSpan.textContent = `折線圖呈現 ${countries.join("、")} 等 ${countries.length} 個國家在 2015-2024 年間的攻擊次數變化對比。`;
    } else if (country === "all") {
        descSpan.textContent = "折線圖呈現全球 2015 到 2024 年間每年的攻擊次數變化，可觀察長期趨勢和年度波動。";
    } else {
        descSpan.textContent = `折線圖呈現 ${country} 在 2015 到 2024 年間每年的攻擊次數變化，可觀察該國的長期趨勢和年度波動。`;
    }
}

/**
 * 更新時間序列統計數據
 */
function updateTimeSeriesStatistics(stats, country) {
    document.getElementById("timeseries-country-name").textContent = country === "all" ? "全部" : country;
    document.getElementById("timeseries-total").textContent = stats.total ? stats.total.toLocaleString() : "-";
    document.getElementById("timeseries-avg").textContent = stats.average ? Math.round(stats.average).toLocaleString() : "-";

    // 攻擊趨勢
    const trendElement = document.getElementById("timeseries-trend");
    if (stats.trend > 0) {
        trendElement.textContent = `↑ ${stats.trend.toFixed(1)}%`;
        trendElement.className = "text-danger";
    } else if (stats.trend < 0) {
        trendElement.textContent = `↓ ${Math.abs(stats.trend).toFixed(1)}%`;
        trendElement.className = "text-success";
    } else {
        trendElement.textContent = "→ 持平";
        trendElement.className = "text-secondary";
    }

    // 財務損失統計
    document.getElementById("timeseries-total-loss").textContent = stats.total_loss ? `$${stats.total_loss.toFixed(1)}M` : "-";

    // 損失趨勢
    const lossTrendElement = document.getElementById("timeseries-loss-trend");
    if (stats.loss_trend > 0) {
        lossTrendElement.textContent = `↑ ${stats.loss_trend.toFixed(1)}%`;
        lossTrendElement.className = "text-danger";
    } else if (stats.loss_trend < 0) {
        lossTrendElement.textContent = `↓ ${Math.abs(stats.loss_trend).toFixed(1)}%`;
        lossTrendElement.className = "text-success";
    } else {
        lossTrendElement.textContent = "→ 持平";
        lossTrendElement.className = "text-secondary";
    }
}

/**
 * 載入統計資料
 */
async function loadStatistics() {
    try {
        const response = await fetch("/api/statistics");
        const data = await response.json();

        document.getElementById("total-attacks").textContent = data.total_attacks.toLocaleString();
        document.getElementById("unique-countries").textContent = data.unique_countries;
        document.getElementById("attack-types").textContent = data.attack_types;
        document.getElementById("date-range").textContent = data.date_range;
        document.getElementById("most-common-attack").textContent = data.most_common_attack;
        document.getElementById("most-targeted-port").textContent = data.most_targeted_port;
    } catch (error) {
        console.error("Error loading statistics:", error);
    }
}

/**
 * 載入安全漏洞分布堆疊長條圖
 */
async function loadSeverityChart() {
    const chartDiv = document.getElementById("severity-chart");
    if (!chartDiv) return; // 如果元素不存在則跳過

    try {
        const response = await fetch("/api/severity_by_type");
        const data = await response.json();
        chartDiv.classList.remove("loading");
        chartDiv.innerHTML = "";

        // Create stacked bar chart
        const traces = [];
        const colors = [
            '#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3',
            '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd'
        ];

        data.vuln_types.forEach((vulnType, idx) => {
            const seriesData = data.series[vulnType];
            traces.push({
                type: 'bar',
                name: vulnType,
                x: seriesData.attack_types,
                y: seriesData.counts,
                marker: {
                    color: colors[idx % colors.length]
                }
            });
        });

        const layout = {
            title: {
                text: '各攻擊類型的安全漏洞分布',
                font: { family: 'Microsoft JhengHei, Arial', size: 16 }
            },
            xaxis: {
                title: '攻擊類型',
                font: { family: 'Microsoft JhengHei, Arial' }
            },
            yaxis: {
                title: '事件數量',
                font: { family: 'Microsoft JhengHei, Arial' }
            },
            barmode: 'stack',
            height: 500,
            font: { family: 'Microsoft JhengHei, Arial', size: 12 },
            legend: {
                title: { text: '安全漏洞類型' }
            }
        };

        Plotly.newPlot("severity-chart", traces, layout, {
            responsive: true,
            displayModeBar: true
        });
    } catch (error) {
        console.error("Error loading severity chart:", error);
        chartDiv.classList.remove("loading");
        chartDiv.innerHTML = '<div class="alert alert-danger">載入圖表失敗</div>';
    }
}

/**
 * 初始化頁面
 */
function initOverviewPage() {
    loadCountries();
    loadStatistics();
    loadTimeSeries(currentTimeSeriesCountry);
    loadSeverityChart();

    // Time series mode change
    document.getElementById("chart-mode-select").addEventListener("change", function () {
        currentChartMode = this.value;
        const multiSelectDiv = document.getElementById("multi-country-select");
        const singleSelect = document.getElementById("timeseries-country-select");
        const hintSpan = document.getElementById("timeseries-hint");

        if (currentChartMode === "compare") {
            multiSelectDiv.style.display = "block";
            singleSelect.disabled = true;
            hintSpan.textContent = "選擇 2-5 個國家進行趨勢對比分析";
        } else {
            multiSelectDiv.style.display = "none";
            singleSelect.disabled = false;
            hintSpan.textContent = "選擇特定國家可查看該國的年度攻擊趨勢變化";
        }
    });

    // Time series filter apply
    document.getElementById("apply-timeseries-filter").addEventListener("click", function () {
        if (currentChartMode === "compare") {
            const selectedCountries = Array.from(
                document.getElementById("timeseries-multi-country").selectedOptions
            ).map((opt) => opt.value);

            if (selectedCountries.length === 0) {
                alert("請至少選擇一個國家");
                return;
            }
            if (selectedCountries.length > 5) {
                alert("最多只能選擇 5 個國家");
                return;
            }

            loadTimeSeries("all", selectedCountries, "compare");
        } else {
            currentTimeSeriesCountry = document.getElementById("timeseries-country-select").value;
            loadTimeSeries(currentTimeSeriesCountry, [], "single");
        }
    });
}

// 頁面載入時初始化
document.addEventListener("DOMContentLoaded", initOverviewPage);
