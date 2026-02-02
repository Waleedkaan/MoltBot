import React from 'react';

const TimeframeSelector = ({ timeframes, selectedTimeframe, onChange }) => {
    const timeframeLabels = {
        '1s': '1s',
        '1m': '1m',
        '3m': '3m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '1h',
        '2h': '2h',
        '4h': '4h',
        '6h': '6h',
        '8h': '8h',
        '12h': '12h',
        '1d': '1d',
        '3d': '3d',
        '1w': '1w',
        '1M': '1M'
    };

    return (
        <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
                Timeframe
            </label>
            <div className="flex flex-wrap gap-2">
                {timeframes && timeframes.map((tf) => (
                    <button
                        key={tf}
                        onClick={() => onChange(tf)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-300 ${selectedTimeframe === tf
                            ? 'bg-primary-600 text-white shadow-glow-blue scale-105'
                            : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
                            }`}
                    >
                        {timeframeLabels[tf] || tf}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default TimeframeSelector;
