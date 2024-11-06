from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log
from surmount.technical_indicators import RSI, VWAP, ATR, SMA
from datetime import datetime

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["SPY", "QQQ"]
        self.max_position = 0.25
        
    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    @property
    def data(self):
        return []  # No additional data sources needed

    def run(self, data):
        allocation_dict = {ticker: 0 for ticker in self.tickers}
        ohlcv = data["ohlcv"]
        
        if len(ohlcv) < 50:
            return TargetAllocation(allocation_dict)

        for ticker in self.tickers:
            try:
                # Core technical indicators
                rsi = RSI(ticker, ohlcv, 14)
                vwap_20 = VWAP(ticker, ohlcv, 20)
                atr = ATR(ticker, ohlcv, 14)
                sma_50 = SMA(ticker, ohlcv, 50)
                
                if not all([rsi, vwap_20, atr, sma_50]):
                    continue

                current_price = ohlcv[-1][ticker]['close']
                
                # Core Strategy Logic - simplified and robust
                trend_signal = (
                    current_price > sma_50[-1] and    # Above medium-term trend
                    current_price > vwap_20[-1]       # Above institutional support
                )
                
                risk_signal = (
                    35 <= rsi[-1] <= 65              # Not extreme RSI
                )
                
                # Position Sizing
                if trend_signal and risk_signal:
                    # Volatility-adjusted position size
                    volatility = atr[-1]/current_price
                    position_size = self.max_position * (1 - min(volatility * 10, 0.5))
                    
                    # Final position size with limits
                    allocation_dict[ticker] = min(position_size, self.max_position)
                    
                log(f"{ticker} Position: {allocation_dict[ticker]:.3f}, RSI: {rsi[-1]:.2f}")
                
            except Exception as e:
                log(f"Error processing {ticker}: {str(e)}")
                continue
        
        # Portfolio-level risk management
        total_allocation = sum(allocation_dict.values())
        if total_allocation > 1:
            allocation_dict = {k: v/total_allocation for k, v in allocation_dict.items()}
        
        return TargetAllocation(allocation_dict)