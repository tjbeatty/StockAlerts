class NewsArticle:
    def __init__(self, date_time, title, ticker_object_list, description, url, source):
        self.date_time = date_time
        self.title = title
        self.ticker_object_list = ticker_object_list
        self.description = description
        self.url = url
        self.source = source

    def __getitem__(self, item):
        return item


class CompanyTicker:
    def __init__(self, ticker, exchange):
        self.ticker = ticker
        self.exchange = exchange

    def __getitem__(self, item):
        return item

