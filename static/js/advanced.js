/**
 * 進階分析頁面 - Plotly.js 圖表
 * Advanced page - Sankey diagram and Treemap
 */

/**
 * 載入 Sankey 圖
 */
async function loadSankey() {
    const chartDiv = document.getElementById("sankey-chart");
    try {
        const response = await fetch("/api/sankey");
        const data = await response.json();
        chartDiv.classList.remove("loading");
        chartDiv.innerHTML = "";

        // Create Sankey diagram
        const trace = {
            type: "sankey",
            orientation: "h",
            node: {
                pad: 15,
                thickness: 20,
                line: {
                    color: "black",
                    width: 0.5,
                },
                label: data.nodes,
                color: data.node_colors,
                hovertemplate: "<b>%{label}</b><br>總攻擊次數: %{value}<extra></extra>",
            },
            link: {
                source: data.sources,
                target: data.targets,
                value: data.values,
                color: "rgba(0,0,0,0.2)",
                hovertemplate: "<b>%{source.label} → %{target.label}</b><br>攻擊次數: %{value}<extra></extra>",
            },
        };

        const layout = {
            title: {
                text: "攻擊流向：國家 → 攻擊類型 → 目標產業",
                font: { family: "Microsoft JhengHei, Arial", size: 16 },
            },
            font: {
                family: "Microsoft JhengHei, Arial",
                size: 12,
            },
            height: 700,
        };

        Plotly.newPlot("sankey-chart", [trace], layout, {
            responsive: true,
            displayModeBar: true,
        });
    } catch (error) {
        console.error("Error loading Sankey diagram:", error);
        chartDiv.classList.remove("loading");
        chartDiv.innerHTML =
            '<div class="alert alert-danger">載入 Sankey 圖失敗：' + error.message + "</div>";
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

        // Color scale mapping
        const colorScales = {
            default: "RdYlGn",
            viridis: "Viridis",
            plasma: "Plasma",
            inferno: "Inferno",
        };

        // Create Treemap
        const trace = {
            type: "treemap",
            labels: data.labels,
            parents: data.parents,
            values: data.values,
            textposition: "middle center",
            marker: {
                colors: data.values,
                colorscale: colorScales[data.colorscheme],
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
        });
    } catch (error) {
        console.error("Error loading Treemap:", error);
        chartDiv.classList.remove("loading");
        chartDiv.innerHTML =
            '<div class="alert alert-danger">載入 Treemap 失敗：' + error.message + "</div>";
    }
}

/**
 * 初始化進階分析頁面
 */
function initAdvancedPage() {
    loadSankey();
    loadTreemap();
}

// 頁面載入時初始化
document.addEventListener("DOMContentLoaded", initAdvancedPage);
