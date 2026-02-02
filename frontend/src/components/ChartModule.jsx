import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

const ChartModule = ({ marketData, prediction }) => {
    const chartContainerRef = useRef(null);
    const chartRef = useRef(null);
    const candlestickSeriesRef = useRef(null);
    const emaFastSeriesRef = useRef(null);
    const emaSlowSeriesRef = useRef(null);
    const bbUpperSeriesRef = useRef(null);
    const bbLowerSeriesRef = useRef(null);
    const targetSeriesRef = useRef(null);

    const [legendData, setLegendData] = React.useState(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        // Create chart
        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: 500,
            layout: {
                background: { color: 'transparent' },
                textColor: '#9CA3AF',
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
            },
            crosshair: {
                mode: 1,
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                timeVisible: true,
                secondsVisible: true,
            },
        });

        // Add candlestick series
        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderVisible: false,
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        });

        // Initialize study series
        emaFastSeriesRef.current = chart.addLineSeries({
            color: '#3b82f6',
            lineWidth: 2,
            lineType: 0,
            title: 'EMA 9'
        });
        emaSlowSeriesRef.current = chart.addLineSeries({
            color: '#f59e0b',
            lineWidth: 2,
            lineType: 0,
            title: 'EMA 21'
        });

        // BB Area/Bands
        bbUpperSeriesRef.current = chart.addLineSeries({
            color: 'rgba(156, 163, 175, 0.4)',
            lineWidth: 1,
            lineStyle: 2,
            title: 'BB'
        });
        bbLowerSeriesRef.current = chart.addLineSeries({
            color: 'rgba(156, 163, 175, 0.4)',
            lineWidth: 1,
            lineStyle: 2,
            title: 'BB'
        });

        targetSeriesRef.current = chart.addLineSeries({
            color: '#ef4444',
            lineWidth: 2,
            lineStyle: 2,
            title: 'Target',
            lastValueVisible: true,
            priceLineVisible: true,
        });

        // Legend tracking
        chart.subscribeCrosshairMove((param) => {
            if (param.time || param.point) {
                const data = {
                    time: param.time,
                    price: param.seriesData.get(candlestickSeries),
                    emaFast: param.seriesData.get(emaFastSeriesRef.current),
                    emaSlow: param.seriesData.get(emaSlowSeriesRef.current),
                    bbUpper: param.seriesData.get(bbUpperSeriesRef.current),
                    bbLower: param.seriesData.get(bbLowerSeriesRef.current),
                };
                setLegendData(data);
            } else {
                setLegendData(null);
            }
        });

        chartRef.current = chart;
        candlestickSeriesRef.current = candlestickSeries;

        // Handle resize
        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({
                    width: chartContainerRef.current.clientWidth
                });
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, []);

    useEffect(() => {
        if (!marketData || !marketData.data || !candlestickSeriesRef.current || !chartRef.current) return;

        // Convert data to lightweight-charts format
        const chartData = marketData.data.map(d => ({
            time: new Date(d.timestamp).getTime() / 1000,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
        }));

        candlestickSeriesRef.current.setData(chartData);

        // Update studies
        if (marketData.data.length > 0) {
            const timeData = marketData.data.map(d => new Date(d.timestamp).getTime() / 1000);

            // EMA Fast
            if (marketData.data[0].ema_fast) {
                emaFastSeriesRef.current.setData(marketData.data.map((d, i) => ({ time: timeData[i], value: d.ema_fast })));
            } else {
                emaFastSeriesRef.current.setData([]);
            }

            // EMA Slow
            if (marketData.data[0].ema_slow) {
                emaSlowSeriesRef.current.setData(marketData.data.map((d, i) => ({ time: timeData[i], value: d.ema_slow })));
            } else {
                emaSlowSeriesRef.current.setData([]);
            }

            // Bollinger Bands
            if (marketData.data[0].bollinger_upper) {
                bbUpperSeriesRef.current.setData(marketData.data.map((d, i) => ({ time: timeData[i], value: d.bollinger_upper })));
                bbLowerSeriesRef.current.setData(marketData.data.map((d, i) => ({ time: timeData[i], value: d.bollinger_lower })));
            } else {
                bbUpperSeriesRef.current.setData([]);
                bbLowerSeriesRef.current.setData([]);
            }

            // Target Price
            if (prediction && prediction.final && prediction.final.target_price) {
                targetSeriesRef.current.applyOptions({
                    color: prediction.final.signal === 'BUY' ? '#10b981' : '#ef4444',
                });
                const targetData = chartData.map(d => ({
                    time: d.time,
                    value: prediction.final.target_price,
                }));
                targetSeriesRef.current.setData(targetData);
            } else {
                targetSeriesRef.current.setData([]);
            }
        }
    }, [marketData, prediction]);

    return (
        <div className="glass-card p-4 animate-slide-up relative">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Price Chart</h3>
                {prediction && prediction.final && prediction.final.target_price && (
                    <div className="flex items-center gap-2 text-sm">
                        <span className="text-gray-400">Target:</span>
                        <span className={prediction.final.signal === 'BUY' ? 'text-success-500' : 'text-danger-500'}>
                            ${prediction.final.target_price.toLocaleString()}
                        </span>
                    </div>
                )}
            </div>

            {/* HUD Legend Overlay */}
            <div className="absolute top-16 left-8 z-10 pointer-events-none flex flex-col gap-1 text-[11px] font-mono">
                {legendData ? (
                    <>
                        <div className="flex gap-3 text-white bg-black/40 px-2 py-1 rounded backdrop-blur-sm">
                            <span>O: <span className="text-success-400">{legendData.price?.open?.toFixed(2)}</span></span>
                            <span>H: <span className="text-success-400">{legendData.price?.high?.toFixed(2)}</span></span>
                            <span>L: <span className="text-danger-400">{legendData.price?.low?.toFixed(2)}</span></span>
                            <span>C: <span className="text-success-400">{legendData.price?.close?.toFixed(2)}</span></span>
                        </div>
                        <div className="flex gap-4 mt-1">
                            <div className="flex items-center gap-1.5 bg-black/40 px-2 py-1 rounded backdrop-blur-sm">
                                <div className="w-2 h-2 rounded-full bg-[#3b82f6]" />
                                <span className="text-gray-300">EMA 9:</span>
                                <span className="text-white">{legendData.emaFast?.value?.toFixed(2) || 'N/A'}</span>
                            </div>
                            <div className="flex items-center gap-1.5 bg-black/40 px-2 py-1 rounded backdrop-blur-sm">
                                <div className="w-2 h-2 rounded-full bg-[#f59e0b]" />
                                <span className="text-gray-300">EMA 21:</span>
                                <span className="text-white">{legendData.emaSlow?.value?.toFixed(2) || 'N/A'}</span>
                            </div>
                            <div className="flex items-center gap-1.5 bg-black/40 px-2 py-1 rounded backdrop-blur-sm">
                                <div className="w-2 h-0.5 bg-gray-400 opacity-40" />
                                <span className="text-gray-300">BB:</span>
                                <span className="text-white">
                                    {legendData.bbUpper?.value?.toFixed(2)} / {legendData.bbLower?.value?.toFixed(2)}
                                </span>
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="text-gray-500 text-xs bg-black/20 px-2 py-1 rounded">Hover over chart for details</div>
                )}
            </div>

            <div ref={chartContainerRef} className="rounded-lg overflow-hidden border border-white/5" />
        </div>
    );
};

export default ChartModule;
