# TODO - Change to ticker object list wherever an Article object exists

class NewsArticle:
    def __init__(self, date, title, ticker_object_list, description, url, source):
        self.date = date
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

