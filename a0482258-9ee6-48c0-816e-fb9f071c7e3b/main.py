from surmount.base_class import Strategy, TargetAllocation
from surmount.data import InsiderTrading, SocialSentiment

class TradingStrategy(Strategy):
    def __init__(self):
        self.ticker = "AAPL"
        self.data_list = [InsiderTrading(self.ticker), SocialSentiment(self.ticker)]

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return [self.ticker]

    @property
    def data(self):
        return self.data_list

    def run(self, data):
        allocation = 0.5  # Start with a neutral allocation
        insider_activities = data[("insider_trading", self.ticker)]
        social_sentiments = data[("social_sentiment", self.ticker)]

        if insider_activities and social_sentiments:
            last_insider_activity = insider_activities[-1]
            last_social_sentiment = social_sentiments[-1]

            # Analyze insider trading activity
            insider_bias = "sell" if last_insider_activity['transactionType'].lower().startswith("s") else "buy"

            # Analyze social sentiment
            social_bias = "positive" if last_social_sentiment['twitterSentiment'] > 0.5 else "negative"

            # Strategy logic
            if insider_bias == "buy" and social_bias == "positive":
                allocation = 0.75  # Increase allocation if both indicators are positive
            elif insider_bias == "sell" and social_bias == "negative":
                allocation = 0.25  # Decrease allocation if both indicators are negative

        # Return the target allocation for AAPL
        return TargetAllocation({self.ticker: allocation})