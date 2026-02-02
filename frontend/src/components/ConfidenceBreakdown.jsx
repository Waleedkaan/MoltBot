import React from 'react';

const ConfidenceBreakdown = ({ prediction, visibleSections }) => {
    if (!prediction || !prediction.breakdown) {
        return null;
    }

    const { strategy, ml, news } = prediction.breakdown;

    const sources = [
        { name: 'Strategy', data: strategy, visible: visibleSections?.strategy },
        { name: 'ML Models', data: ml, visible: visibleSections?.ml },
        { name: 'News/Sentiment', data: news, visible: visibleSections?.news }
    ];

    const getSignalColor = (signal) => {
        if (signal === 'BUY') return 'text-success-500';
        if (signal === 'SELL') return 'text-danger-500';
        return 'text-gray-400';
    };

    return (
        <div className="glass-card p-6 animate-slide-up">
            <h3 className="text-lg font-semibold text-gray-300 mb-4">Confidence Breakdown</h3>

            <div className="space-y-4">
                {sources.map((source, idx) => (
                    source.visible && source.data && (
                        <div key={idx} className="transition-all duration-300">
                            {/* Source Name & Signal */}
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm text-gray-300 font-medium">{source.name}</span>
                                    <span className="text-xs text-gray-500">({source.data.weight})</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className={`text-sm font-bold ${getSignalColor(source.data.signal)}`}>
                                        {source.data.signal}
                                    </span>
                                    <span className="text-sm text-gray-400">
                                        {source.data.confidence.toFixed(1)}%
                                    </span>
                                </div>
                            </div>

                            {/* Progress Bar */}
                            <div className="progress-bar">
                                <div
                                    className={`progress-fill ${source.data.signal === 'BUY' ? 'bg-success-500' :
                                            source.data.signal === 'SELL' ? 'bg-danger-500' :
                                                'bg-gray-500'
                                        }`}
                                    style={{ width: `${source.data.confidence}%` }}
                                />
                            </div>
                        </div>
                    )
                ))}
            </div>

            {/* Final Confidence */}
            {visibleSections?.final && prediction.final && (
                <div className="mt-6 pt-4 border-t border-white/20">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-semibold text-white">Final Confidence</span>
                        <span className={`text-lg font-bold ${prediction.final.confidence >= 75 ? 'text-success-500' :
                                prediction.final.confidence >= 60 ? 'text-primary-400' :
                                    'text-gray-400'
                            }`}>
                            {prediction.final.confidence.toFixed(1)}%
                        </span>
                    </div>
                    <div className="progress-bar">
                        <div
                            className="progress-fill bg-gradient-to-r from-primary-600 via-purple-500 to-primary-400"
                            style={{ width: `${prediction.final.confidence}%` }}
                        />
                    </div>
                </div>
            )}
        </div>
    );
};

export default ConfidenceBreakdown;
