import React from 'react';

const CoinSelector = ({ coins, selectedCoin, onChange }) => {
    return (
        <div className="relative">
            <label className="block text-sm font-medium text-gray-300 mb-2">
                Select Coin
            </label>
            <div className="relative">
                <select
                    value={selectedCoin}
                    onChange={(e) => onChange(e.target.value)}
                    className="input-field w-full appearance-none pr-10 cursor-pointer"
                >
                    {coins && coins.map((coin) => (
                        <option key={coin.symbol} value={coin.symbol} className="bg-dark-900">
                            {coin.name} ({coin.symbol})
                        </option>
                    ))}
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </div>
            </div>
        </div>
    );
};

export default CoinSelector;
