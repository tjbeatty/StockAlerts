import re
from stock_alert_classes import CompanyTicker, NewsArticle
from selenium import webdriver
import datetime


def is_english_story(url):
    """
    Checks url for language
    :param url: URL of article
    :return: True if it's an English artcle, False if not
    """
    if '/en/' in url:
        return True
    else:
        return False


def initialize_browser(arguments='headless'):
    """
    Initializes a browser for Selenium
    :param arguments: arguments for browser setup
    :return: Browser object
    """
    options = webdriver.ChromeOptions()
    options.add_argument(arguments)
    browser = webdriver.Chrome(options=options)
    return browser


def get_ticker_objects_from_description(description):
    """
    Pulls tickers from text
    :param description: Input text to look for ticker symbols
    :return: Ticker objects (including exchanges)
    """
    exchanges = ['nasdaq', 'nyse', 'nasdaqgs']
    tickers_found = []
    for exchange in exchanges:
        exchange_col = exchange + ':'
        index = [i for i in range(len(description)) if description.lower().startswith(exchange_col, i)]
        for j in index:
            exchange_found = exchange.upper()
            first_split = description[j:].lower().split(exchange_col)[1].replace(' ', '')
            ticker = re.split('[^a-z]', first_split)[0].upper()
            ticker_object = CompanyTicker(ticker, exchange_found)
            tickers_found.append(ticker_object)

    return tickers_found


def get_exchange_tickers_description(description):
    ticker_object_list = get_ticker_objects_from_description(description)
    exchange_ticker_list = [ticker.exchange + ': ' + ticker.ticker for ticker in ticker_object_list]
    return exchange_ticker_list


def normalize_date_return_object(date_string):
    """
    Pulls in a date text in many formats and returns a date object
    :param date_string: Date text
    :return: Date object
    """
    months_list = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                   'November', 'December']
    short_months_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    timezones = ['ET', 'CT', 'MT', 'PT', 'EDT', 'CDT', 'MDT', 'PDT', 'EST', 'CST', 'MST', 'PST']
    month_text_in_date = [ele for ele in months_list if (ele in date_string)]
    short_month_text_in_date = [ele for ele in short_months_list if (ele in date_string)]
    timezone_text_in_date = [ele for ele in timezones if (ele in date_string)]
    if month_text_in_date and "," in date_string:
        if ':' in date_string:
            if ' pm' in date_string.lower() or ' am' in date_string.lower():
                date_string = date_string[0:date_string.index(':') + 6]
                date_object = datetime.datetime.strptime(date_string, '%B %d, %Y %H:%M %p')
                print(date_object)
            elif 'pm' in date_string.lower() or 'am' in date_string.lower():
                date_string = date_string[0:date_string.index(':') + 5]
                date_object = datetime.datetime.strptime(date_string, '%B %d, %Y %H:%M%p')
            else:
                date_string = date_string[0:date_string.index(':') + 3]
                date_object = datetime.datetime.strptime(date_string, '%B %d, %Y %H:%M')
        else:
            date_object = datetime.datetime.strptime(date_string, '%B %d, %Y')

    elif short_month_text_in_date and ',' in date_string:
        date_object = datetime.datetime.strptime(date_string, '%b %d, %Y')

    elif '-' in date_string or '/' in date_string:
        if '-' in date_string:
            date_string = date_string.replace('-', '/')
        date_list = date_string.split('/')
        if len(date_list[2]) == 4:
            date_object = datetime.datetime.strptime(date_string, '%m/%d/%Y')
        elif len(date_list[0]) == 4:
            date_object = datetime.datetime.strptime(date_string, '%Y/%m/%d')
        else:
            date_object = datetime.datetime.strptime(date_string, '%m/%d/%y')

    if date_object:
        return date_object

