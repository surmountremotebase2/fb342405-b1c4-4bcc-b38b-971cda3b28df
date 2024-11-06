from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log
from surmount.technical_indicators import RSI, VWAP, ATR, SMA
from surmount.data import StLouisFinancialStressIndex, Ratios

class TradingStrategy(Strategy):
    def __init__(self):
        # Focus on highly liquid instruments
        self.tickers = ["SPY", "QQQ"]  # Reduced to most liquid ETFs for better execution
        self.data_list = [
            StLouisFinancialStressIndex(),
            *[Ratios(ticker) for ticker in self.tickers],
        ]
        self.max_position = 0.25
        
    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    @property
    def data(self):
        return self.data_list

    def run(self, data):
        allocation_dict = {ticker: 0 for ticker in self.tickers}
        ohlcv = data["ohlcv"]
        
        if len(ohlcv) < 50:
            return TargetAllocation(allocation_dict)

        # Market regime check
        stress_index = data.get(("stlouis_financial_stress_index"), [])
        market_stress = stress_index[-1]['value'] if stress_index else 0
        
        # Risk adjustment based on market stress
        max_position = self.max_position * (0.35 if market_stress > 0 else 1.0)

        for ticker in self.tickers:
            try:
                # Core technical indicators - only the most essential ones
                rsi = RSI(ticker, ohlcv, 14)
                vwap_20 = VWAP(ticker, ohlcv, 20)
                atr = ATR(ticker, ohlcv, 14)
                sma_50 = SMA(ticker, ohlcv, 50)
                
                if not all([rsi, vwap_20, atr, sma_50]):
                    continue

                current_price = ohlcv[-1][ticker]['close']
                
                # Get fundamental data
                ratios = data.get(("ratios", ticker), [])
                if not ratios:
                    continue
                latest_ratios = ratios[-1]
                
                # Core Strategy Logic - simplified and robust
                trend_signal = (
                    current_price > sma_50[-1] and    # Above medium-term trend
                    current_price > vwap_20[-1]       # Above institutional support
                )
                
                risk_signal = (
                    35 <= rsi[-1] <= 65              # Not extreme RSI, tightened range
                )
                
                # Position Sizing
                if trend_signal and risk_signal:
                    # Volatility-adjusted position size
                    volatility = atr[-1]/current_price
                    position_size = max_position * (1 - min(volatility * 10, 0.5))
                    
                    # Quality adjustment based on fundamentals
                    if latest_ratios['returnOnEquity'] > 0.15:
                        position_size *= 1.1  # Reduced multiplier for more stability
                        
                    # Final position size with limits
                    allocation_dict[ticker] = min(position_size, max_position)
                    
                log(f"{ticker} Position: {allocation_dict[ticker]:.3f}, RSI: {rsi[-1]:.2f}")
                
            except Exception as e:
                log(f"Error processing {ticker}: {str(e)}")
                continue
        
        # Portfolio-level risk management
        total_allocation = sum(allocation_dict.values())
        if total_allocation > 1:
            allocation_dict = {k: v/total_allocation for k, v in allocation_dict.items()}
        
        return TargetAllocation(allocation_dict)