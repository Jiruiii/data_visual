/**
 * 地圖分析頁面 - Plotly.js 動態地圖
 * Map page - Animated choropleth map
 */

/**
 * 載入地圖資料並繪製動態地圖
 */
async function loadMapData() {
    const chartDiv = document.getElementById('map-chart');
    try {
        const response = await fetch('/api/map_data');
        const mapData = await response.json();

        if (mapData.error) {
            throw new Error(mapData.error);
        }

        // Update global statistics
        updateGlobalStatistics(mapData.statistics);

        chartDiv.classList.remove('loading');
        chartDiv.innerHTML = '';

        // Prepare frames and slider steps
        const frames = [];
        const sliderSteps = [];

        // Calculate global min/max for consistent color scale
        let allLosses = [];
        mapData.years.forEach(year => {
            const yearData = mapData.data_by_year[year.toString()];
            if (yearData && yearData.losses) {
                allLosses = allLosses.concat(yearData.losses);
            }
        });
        const minLoss = Math.min(...allLosses);
        const maxLoss = Math.max(...allLosses);

        // Create frames for each year
        mapData.years.forEach((year, index) => {
            const yearData = mapData.data_by_year[year.toString()];

            frames.push({
                name: year.toString(),
                data: [{
                    locations: yearData.countries,
                    z: yearData.losses,
                    text: yearData.countries
                }]
            });

            sliderSteps.push({
                label: year.toString(),
                method: 'animate',
                args: [[year.toString()], {
                    mode: 'immediate',
                    transition: { duration: 300 },
                    frame: { duration: 300, redraw: true }
                }]
            });
        });

        // Initial data (first year)
        const firstYearData = mapData.data_by_year[mapData.years[0].toString()];
        const data = [{
            type: 'choropleth',
            locationmode: 'country names',
            locations: firstYearData.countries,
            z: firstYearData.losses,
            text: firstYearData.countries,
            colorscale: [
                [0, 'rgb(247, 251, 255)'],
                [0.2, 'rgb(198, 219, 239)'],
                [0.4, 'rgb(158, 202, 225)'],
                [0.6, 'rgb(107, 174, 214)'],
                [0.8, 'rgb(49, 130, 189)'],
                [1, 'rgb(8, 81, 156)']
            ],
            autocolorscale: false,
            reversescale: false,
            zauto: false,
            zmin: minLoss,
            zmax: maxLoss,
            marker: {
                line: {
                    color: 'rgb(180,180,180)',
                    width: 0.5
                }
            },
            colorbar: {
                title: {
                    text: '財務損失<br>(百萬美元)',
                    side: 'right'
                },
                thickness: 20,
                len: 0.7,
                tickformat: ',.0f',
                ticksuffix: 'M'
            },
            hovertemplate: '<b>%{text}</b><br>財務損失: $%{z:,.2f}M<extra></extra>'
        }];

        // Layout with animation controls
        const layout = {
            title: {
                text: '全球網路攻擊財務損失分布<br>2015 - 2024',
                font: {
                    family: 'Microsoft JhengHei, Arial',
                    size: 18
                }
            },
            geo: {
                showframe: false,
                showcoastlines: true,
                projection: {
                    type: 'natural earth'
                },
                landcolor: 'rgb(217, 217, 217)',
                showland: true
            },
            height: 650,
            font: {
                family: 'Microsoft JhengHei, Arial',
                size: 14
            },
            // Play/Pause buttons
            updatemenus: [{
                x: 0.1,
                y: 0,
                yanchor: 'top',
                xanchor: 'right',
                showactive: false,
                direction: 'left',
                type: 'buttons',
                pad: { t: 87, r: 10 },
                buttons: [{
                    method: 'animate',
                    args: [null, {
                        fromcurrent: true,
                        transition: { duration: 300 },
                        frame: { duration: 800, redraw: true }
                    }],
                    label: '▶ 播放'
                }, {
                    method: 'animate',
                    args: [[null], {
                        mode: 'immediate',
                        transition: { duration: 0 },
                        frame: { duration: 0, redraw: false }
                    }],
                    label: '⏸ 暫停'
                }]
            }],
            // Year slider
            sliders: [{
                active: 0,
                steps: sliderSteps,
                x: 0.1,
                len: 0.9,
                xanchor: 'left',
                y: 0,
                yanchor: 'top',
                pad: { t: 50, b: 10 },
                currentvalue: {
                    visible: true,
                    prefix: '年份: ',
                    xanchor: 'right',
                    font: {
                        size: 20,
                        color: '#666'
                    }
                },
                transition: {
                    duration: 300,
                    easing: 'cubic-in-out'
                }
            }]
        };

        // Create plot and add frames
        Plotly.newPlot('map-chart', data, layout, {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            displaylogo: false
        }).then(function () {
            Plotly.addFrames('map-chart', frames);
        });

    } catch (error) {
        console.error('Error loading map data:', error);
        chartDiv.classList.remove('loading');
        chartDiv.innerHTML =
            '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> 載入地圖失敗：' + error.message + '</div>';
    }
}

/**
 * 更新全域統計數據
 * @param {Object} stats - 統計數據
 */
function updateGlobalStatistics(stats) {
    document.getElementById('total-loss').textContent = `$${stats.total_loss.toFixed(1)}M`;
    document.getElementById('avg-loss').textContent = `$${stats.avg_loss_per_country.toFixed(1)}M`;
    document.getElementById('max-country').textContent = stats.max_loss_country;
    document.getElementById('max-loss').textContent = `$${stats.max_loss_value.toFixed(1)}M`;
    document.getElementById('map-stats').style.display = 'flex';
}

/**
 * 初始化地圖頁面
 */
function initMapPage() {
    loadMapData();

    // Handle window resize
    window.addEventListener('resize', function () {
        if (document.getElementById('map-chart').children.length > 0) {
            Plotly.Plots.resize('map-chart');
        }
    });
}

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', initMapPage);
