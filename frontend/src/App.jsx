import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
// MoltBot Dashboard v1.0.1
import { getCoins, getTimeframes, getMarketData, getPrediction, getUserSettings, updateUserSettings, getWsUrl, updateBaseUrl } from './services/api';
import CoinSelector from './components/CoinSelector';
import TimeframeSelector from './components/TimeframeSelector';
import SignalCard from './components/SignalCard';
import ConfidenceBreakdown from './components/ConfidenceBreakdown';
import ChartModule from './components/ChartModule';

function App() {
    const [selectedCoin, setSelectedCoin] = useState('BTC');
    const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
    const [visibleSections, setVisibleSections] = useState({
        strategy: true,
        ml: true,
        news: true,
        final: true,
        predicted_price: true
    });
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [tempUrl, setTempUrl] = useState(localStorage.getItem('MOLTBOT_API_URL') || '');

    // Fetch coins
    const { data: coins } = useQuery({
        queryKey: ['coins'],
        queryFn: getCoins
    });

    // Fetch timeframes
    const { data: timeframes } = useQuery({
        queryKey: ['timeframes'],
        queryFn: getTimeframes
    });

    const [wsMarketData, setWsMarketData] = useState(null);
    const [wsPrediction, setWsPrediction] = useState(null);

    // Initial load of market data (for fast startup)
    const { data: initialMarketData, isLoading: isLoadingMarket } = useQuery({
        queryKey: ['marketDataInitial', selectedCoin, selectedTimeframe],
        queryFn: () => getMarketData(selectedCoin, selectedTimeframe, 100),
    });

    // WebSocket Connection for Live Updates
    useEffect(() => {
        const wsUrl = getWsUrl();
        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log('Connected to market websocket');
            // Subscribe to selected coin/timeframe
            socket.send(JSON.stringify({
                coin: selectedCoin,
                timeframe: selectedTimeframe
            }));
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'full_update') {
                setWsMarketData({
                    coin: data.coin,
                    timeframe: data.timeframe,
                    data: data.market_data
                });
                setWsPrediction(data.prediction);
            }
        };

        socket.onclose = () => console.log('WebSocket disconnected');

        return () => socket.close();
    }, [selectedCoin, selectedTimeframe]);

    const marketData = wsMarketData || initialMarketData;
    const prediction = wsPrediction;
    const isLoadingPrediction = !prediction && !wsPrediction;

    // Toggle visibility
    const toggleSection = (section) => {
        setVisibleSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    return (
        <div className="min-h-screen p-4 md:p-8">
            {/* Header */}
            <div className="max-w-7xl mx-auto mb-8">
                <div className="glass-card p-6">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h1 className="text-4xl font-bold text-gradient mb-2">MoltBot</h1>
                            <p className="text-gray-400">Advanced Crypto Trading Platform</p>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                            <button
                                onClick={() => setIsSettingsOpen(true)}
                                className="text-xs text-gray-400 hover:text-white transition-colors bg-white/5 px-2 py-1 rounded"
                            >
                                ⚙️ Connection Settings
                            </button>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 bg-success-500 rounded-full animate-pulse"></div>
                                <span className="text-sm text-gray-400">Live</span>
                            </div>
                        </div>
                    </div>

                    {/* Controls */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <CoinSelector
                            coins={coins}
                            selectedCoin={selectedCoin}
                            onChange={setSelectedCoin}
                        />
                        <TimeframeSelector
                            timeframes={timeframes}
                            selectedTimeframe={selectedTimeframe}
                            onChange={setSelectedTimeframe}
                        />
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto grid grid-cols-1 xl:grid-cols-3 gap-6">
                {/* Chart - Takes 2 columns */}
                <div className="xl:col-span-2">
                    {isLoadingMarket ? (
                        <div className="glass-card p-6 h-[550px] flex items-center justify-center">
                            <div className="text-center">
                                <div className="w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                                <p className="text-gray-400">Loading chart...</p>
                            </div>
                        </div>
                    ) : (
                        <ChartModule marketData={marketData} prediction={prediction} />
                    )}
                </div>

                {/* Signal & Breakdown - Takes 1 column */}
                <div className="space-y-6">
                    {isLoadingPrediction ? (
                        <div className="glass-card p-6 h-64 flex items-center justify-center">
                            <div className="text-center">
                                <div className="w-10 h-10 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                                <p className="text-gray-400">Analyzing...</p>
                            </div>
                        </div>
                    ) : (
                        <>
                            <SignalCard prediction={prediction} />
                            <ConfidenceBreakdown prediction={prediction} visibleSections={visibleSections} />
                        </>
                    )}
                </div>
            </div>

            {/* Visibility Toggles */}
            <div className="max-w-7xl mx-auto mt-6">
                <div className="glass-card p-6">
                    <h3 className="text-sm font-semibold text-gray-300 mb-4">Visibility Controls</h3>
                    <div className="flex flex-wrap gap-3">
                        {[
                            { key: 'strategy', label: 'Strategy %' },
                            { key: 'ml', label: 'ML %' },
                            { key: 'news', label: 'News %' },
                            { key: 'final', label: 'Final %' },
                            { key: 'predicted_price', label: 'Predicted Price' }
                        ].map(({ key, label }) => (
                            <button
                                key={key}
                                onClick={() => toggleSection(key)}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${visibleSections[key]
                                    ? 'bg-primary-600 text-white shadow-glow-blue'
                                    : 'bg-white/5 text-gray-400 hover:bg-white/10'
                                    }`}
                            >
                                {label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Disclaimer */}
            <div className="max-w-7xl mx-auto mt-6">
                <div className="glass-card p-4 border-l-4 border-yellow-500">
                    <p className="text-sm text-yellow-500">
                        ⚠️ <strong>Disclaimer:</strong> Predictions are probability-based and not guaranteed. Trading cryptocurrencies involves significant risk. Always do your own research and never invest more than you can afford to lose.
                    </p>
                </div>
            </div>
            {/* Connection Settings Modal */}
            {isSettingsOpen && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="glass-card max-w-md w-full p-8 relative">
                        <h2 className="text-2xl font-bold mb-4">Backend Connection</h2>
                        <p className="text-gray-400 text-sm mb-6">
                            Enter your local PC's tunnel URL (e.g. from localtunnel or ngrok) to connect the dashboard to your AI engine.
                        </p>
                        <input
                            type="text"
                            className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-white mb-6"
                            placeholder="https://your-tunnel.loca.lt"
                            value={tempUrl}
                            onChange={(e) => setTempUrl(e.target.value)}
                        />
                        <div className="flex gap-4">
                            <button
                                onClick={() => {
                                    updateBaseUrl(tempUrl);
                                    setIsSettingsOpen(false);
                                    window.location.reload();
                                }}
                                className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-bold py-3 rounded-lg transition-colors"
                            >
                                Connect & Save
                            </button>
                            <button
                                onClick={() => setIsSettingsOpen(false)}
                                className="flex-1 bg-white/5 hover:bg-white/10 text-white font-bold py-3 rounded-lg transition-colors"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;
