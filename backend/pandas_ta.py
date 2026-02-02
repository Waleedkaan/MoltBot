"""
Simple Shim for pandas_ta using ta library
Allows code to run without numba dependency
"""
import pandas as pd
import numpy as np
import ta as ta_lib

def rsi(close, length=14, **kwargs):
    return ta_lib.momentum.rsi(close, window=length)

def ema(close, length=10, **kwargs):
    return ta_lib.trend.ema_indicator(close, window=length)

def sma(close, length=10, **kwargs):
    return ta_lib.trend.sma_indicator(close, window=length)

def macd(close, fast=12, slow=26, signal=9, **kwargs):
    # returns a DataFrame with MACD_12_26_9, MACDs_12_26_9, MACDh_12_26_9
    m = ta_lib.trend.MACD(close, window_fast=fast, window_slow=slow, window_sign=signal)
    df = pd.DataFrame()
    col_macd = f"MACD_{fast}_{slow}_{signal}"
    col_signal = f"MACDs_{fast}_{slow}_{signal}"
    col_hist = f"MACDh_{fast}_{slow}_{signal}"
    df[col_macd] = m.macd()
    df[col_signal] = m.macd_signal()
    df[col_hist] = m.macd_diff()
    return df

def bbands(close, length=20, std=2, **kwargs):
    # returns BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
    bb = ta_lib.volatility.BollingerBands(close, window=length, window_dev=std)
    df = pd.DataFrame()
    df[f"BBL_{length}_{std}.0"] = bb.bollinger_lband()
    df[f"BBM_{length}_{std}.0"] = bb.bollinger_mavg()
    df[f"BBU_{length}_{std}.0"] = bb.bollinger_hband()
    return df

def atr(high, low, close, length=14, **kwargs):
    return ta_lib.volatility.average_true_range(high, low, close, window=length)
