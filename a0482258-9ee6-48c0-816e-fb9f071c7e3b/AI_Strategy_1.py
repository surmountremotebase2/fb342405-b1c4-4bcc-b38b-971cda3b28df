from surmount.base_class import Strategy, TargetAllocation
from surmount.data import Asset, InsiderTrading, InstitutionalOwnership, SocialSentiment, Ratios
from surmount.technical_indicators import RSI, SMA
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        # InsiderTrading and InstitutionalOwnership are objects built for each ticker
        self.insider_trading_data = [InsiderTrading(ticker) for ticker in self.tickers]
        self.institutional_ownership_data = [InstitutionalOwnership(ticker) for ticker in self.tickers]
        # Assuming SocialSentiment and Ratios data can be accessed similarly
        self.social_sentiment_data = [SocialSentiment(ticker) for ticker in self.tickers]
        self.ratios_data = [Ratios(ticker) for ticker in self.tickers]

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    @property
    def data(self):
        # Combine all data needed for analysis
        return self.insider_trading_data + self.institutional_ownership_data + self.social_sentiment_data + self.ratios_data

    def run(self, data):
        allocation_dict = {}
        eligible_stocks = []

        for ticker in self.tickers:
            # Criteria checks
            insider_buying = any(trade['transactionType'] == 'Buy' for trade in data[InsiderTrading(ticker)][-5:])
            institutional_ownership = data[InstitutionalOwnership(ticker)][-1]['ownershipPercentage'] > 50
            social_sentiment = data[SocialSentiment(ticker)][-1]['averageSentiment'] > 0.5
            debt_equity_ratio = data[Ratios(ticker)][-1]['debtEquityRatio'] < 1
            roe = data[Ratios(ticker)][-1]['returnOnEquity'] > 15

            rsi = RSI(ticker, data, 14)  # Assuming accessing RSI through some function
            rsi_condition = rsi[-1] < 30

            sma20 = SMA(ticker, data, 20)
            sma50 = SMA(ticker, data, 50)
            sma_trend = sma20[-1] > sma50[-1]

            # If all conditions are met, add to eligible_stocks
            if all([insider_buying, institutional_ownership, social_sentiment, 
                    debt_equity_ratio, roe, rsi_condition, sma_trend]):
                eligible_stocks.append(ticker)

        # Allocate equally among eligible stocks or stay in cash
        if eligible_stocks:
            allocation_per_stock = 1 / len(eligible_stocks)
            for stock in eligible_stocks:
                allocation_dict[stock] = allocation_per_stock
        else:
            # If no stock meets the criteria, potentially keep allocation in cash or equivalent (not explicitly modeled here)
            log("No stocks meet the criteria, holding cash")

        return TargetAllocation(allocation_dict)