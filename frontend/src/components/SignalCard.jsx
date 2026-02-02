import React from 'react';

const SignalCard = ({ prediction }) => {
    if (!prediction || !prediction.final) {
        return (
            <div className="glass-card p-6 animate-pulse">
                <div className="h-32 bg-white/10 rounded"></div>
            </div>
        );
    }

    const { final, current_price } = prediction;
    const { signal, confidence, target_price, target_type, meets_threshold } = final;

    const getSignalClass = (sig) => {
        if (sig === 'BUY') return 'signal-buy';
        if (sig === 'SELL') return 'signal-sell';
        return 'signal-neutral';
    };

    const getSignalGlow = (sig) => {
        if (sig === 'BUY') return 'shadow-glow-green';
        if (sig === 'SELL') return 'shadow-glow-red';
        return '';
    };

    return (
        <div className={`glass-card p-6 ${getSignalGlow(signal)} transition-all duration-500 animate-slide-up`}>
            {/* Signal Badge */}
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-300">Trading Signal</h3>
                <span className={getSignalClass(signal)}>
                    {signal}
                </span>
            </div>

            {/* Confidence */}
            <div className="mb-4">
                <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-400">Confidence</span>
                    <span className={`font-bold ${confidence >= 75 ? 'text-success-500' : confidence >= 60 ? 'text-primary-400' : 'text-gray-400'}`}>
                        {confidence.toFixed(1)}%
                    </span>
                </div>
                <div className="progress-bar">
                    <div
                        className={`progress-fill ${signal === 'BUY' ? 'bg-gradient-to-r from-success-600 to-success-400' :
                                signal === 'SELL' ? 'bg-gradient-to-r from-danger-600 to-danger-400' :
                                    'bg-gray-600'
                            }`}
                        style={{ width: `${confidence}%` }}
                    />
                </div>
            </div>

            {/* Current Price */}
            <div className="mb-2">
                <div className="text-sm text-gray-400">Current Price</div>
                <div className="text-2xl font-bold text-white">
                    ${current_price ? current_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '---'}
                </div>
            </div>

            {/* Target Price */}
            {meets_threshold && target_price && (
                <div className="mt-4 pt-4 border-t border-white/10">
                    <div className="flex items-center justify-between">
                        <div>
                            <div className="text-sm text-gray-400">Target {target_type}</div>
                            <div className={`text-xl font-bold ${signal === 'BUY' ? 'text-success-500' : 'text-danger-500'}`}>
                                ${target_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-sm text-gray-400">Move</div>
                            <div className={`text-lg font-semibold ${signal === 'BUY' ? 'text-success-500' : 'text-danger-500'}`}>
                                {((target_price - current_price) / current_price * 100).toFixed(2)}%
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Low Confidence Warning */}
            {!meets_threshold && (
                <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <div className="text-yellow-500 text-sm font-medium">
                        ⚠️ Confidence below threshold - NO TRADE recommended
                    </div>
                </div>
            )}
        </div>
    );
};

export default SignalCard;
