from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log
from surmount.data import InsiderTrading, InstitutionalOwnership, SocialSentiment, Ratios
from surmount.technical_indicators import RSI, SMA

class TradingStrategy(Strategy):

    def __init__(self):
        self.tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        # Initialize data sources following the documented pattern
        self.data_list = []
        # Initialize each data source type separately
        self.data_list = [InsiderTrading(ticker) for ticker in self.tickers]
        self.data_list.extend([InstitutionalOwnership(ticker) for ticker in self.tickers])
        self.data_list.extend([SocialSentiment(ticker) for ticker in self.tickers])
        self.data_list.extend([Ratios(ticker) for ticker in self.tickers])

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
        allocation_dict = {}
        ohlcv_data = data.get("ohlcv")

        for ticker in self.tickers:
            # Get data for the ticker
            insider_trades = data[InsiderTrading(ticker)]
            institutional_data = data[InstitutionalOwnership(ticker)][-1]  # Latest data point
            social_data = data[SocialSentiment(ticker)][-1]
            ratios_data = data[Ratios(ticker)][-1]
            ticker_ohlcv = data["ohlcv"]  # This already contains the properly formatted OHLCV data

            # Check for recent insider buying
            recent_buy = False
            if insider_trades:
                for trade in insider_trades[-5:]:  # Look at last 5 trades
                    if "Buy" in trade.get("transactionType", ""):
                        recent_buy = True
                        break

            # Check for high institutional ownership
            inst_ownership_percent = institutional_data.get("ownershipPercentage", 0)

            # Check for positive social sentiment
            twitter_sentiment = social_data.get("averageSentiment", 0)
            stocktwits_sentiment = social_data.get("stocktwitsSentiment", 0)
            avg_sentiment = (twitter_sentiment + stocktwits_sentiment) / 2

            # Check financial ratios
            debt_equity = ratios_data.get("debtEquityRatio", None)
            return_on_equity = ratios_data.get("returnOnEquity", None)

            # Use technical indicators if sufficient data is available
            if len(ticker_ohlcv) >= 50:
                rsi = RSI(ticker, ohlcv_data, length=14)
                sma_short = SMA(ticker, ohlcv_data, length=20)
                sma_long = SMA(ticker, ohlcv_data, length=50)

                # Check if technical indicators are valid
                indicators_ready = rsi and sma_short and sma_long
                if indicators_ready:
                    # Determine if conditions are met
                    conditions = [
                        recent_buy,
                        inst_ownership_percent > 50,
                        avg_sentiment > 0.5,
                        debt_equity is not None and debt_equity < 1,
                        return_on_equity is not None and return_on_equity > 0.15,
                        rsi[-1] < 30,
                        sma_short[-1] > sma_long[-1]  # Bullish crossover
                    ]

                    if all(conditions):
                        allocation_dict[ticker] = 1 / len(self.tickers)
                    else:
                        allocation_dict[ticker] = 0
                else:
                    allocation_dict[ticker] = 0
            else:
                allocation_dict[ticker] = 0

        # Normalize allocations
        total_allocation = sum(allocation_dict.values())
        if total_allocation > 0:
            allocation_dict = {k: v / total_allocation for k, v in allocation_dict.items()}
        else:
            allocation_dict = {}

        return TargetAllocation(allocation_dict)