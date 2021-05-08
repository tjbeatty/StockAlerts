from bs4 import BeautifulSoup
import urllib.request
import requests
import datetime
from general_functions import normalize_date_return_object
import json

# TODO - Add support for this: GET /stock/{symbol}/advanced-stats


# TODO - Do I need this anymore?
def convert_text_date_for_api(date_string):
    """
    Take a text input and returns a specific date string for use in an API. Probably not useful anymore
    :param date_string:
    :return:
    """
    date_object = datetime.datetime.strptime(date_string, '%B %d, %Y')
    date_out = date_object.strftime('%m/%d/%Y')
    return date_out


def get_daily_response_polygon(ticker, date):
    """
    Gets daiy stock market data for a ticker/date
    :param ticker: Company ticker
    :param date: Date
    :return: Response from API
    """
    date_object = datetime.date.today()

    if '-' in date:
        date = date.replace('-', '/')

    date_list = date.split('/')

    if len(date_list[2]) == 4:
        date_object = datetime.datetime.strptime(date, '%m/%d/%Y')
    elif len(date_list[2]) == 2:
        date_object = datetime.datetime.strptime(date, '%m/%d/%y')

    date_str = date_object.strftime('%Y-%m-%d')
    api_key = '33JLJMtAMWpMBfhGz9nU4P_0CHZhenwd'
    url = 'https://api.polygon.io/v1/open-close/' + ticker + '/' + date_str + '?unadjusted=true&apiKey=' + api_key
    response = requests.get(url)

    return response


def get_percent_change_from_date_polygon(ticker, date):
    """
    Returns the intraday stock percent change for a ticker and date
    :param ticker: Company ticker
    :param date: Date
    :return: Intraday percent change
    """
    api_response = get_daily_response_polygon(ticker, date)
    percent_change = ''
    if api_response.status_code == 200:
        data = api_response.json()
        open_price = data['open']
        close_price = data['close']
        percent_change = (close_price - open_price) / open_price

        # print(percent_change)
    return percent_change


def get_token_iex(token_type='Prod'):
    if token_type.lower() == 'prod':
        token = 'pk_b7f4919ac9bc46499092ab5ad36a59e4'
    elif 'sand' in token_type.lower():
        token = 'Tpk_958d6bd4a69346e2bcbee47881694efa'
    else:
        token = 'pk_b7f4919ac9bc46499092ab5ad36a59e4'
    return token


def get_daily_response_iex(ticker, date, token_type='Prod'):
    """
    Gets daiy stock market data for a ticker/date
    :param ticker: Company ticker
    :param date: Date
    :param token_type: Prod or Sandbox
    :return: Response from API
    """
    date_object = datetime.date.today()

    token = get_token_iex(token_type)
    date_object = normalize_date_return_object(date)

    try:
        date_str = date_object.strftime('%Y%m%d')
        url = 'https://cloud.iexapis.com/stable/stock/' + ticker + '/chart/date/' + date_str + \
              '?chartByDay=true&token=' + token
        print(url)
        response = requests.get(url)
        return response
    except (KeyError, IndexError):
        return {}


# TODO - Add getting shares outstanding so we can calculate market cap on a specific date
def get_shares_outstanding(ticker, token_type='Prod'):
    token = get_token_iex(token_type)
    url = 'https://cloud.iexapis.com/stable/stock/' + ticker + '/stats/sharesOutstanding' + \
          '?token=' + token
    print(url)
    response = requests.get(url)
    data = response.json()
    return data


def get_average_volume(ticker, token_type='Prod'):
    token = get_token_iex(token_type)
    url = 'https://cloud.iexapis.com/stable/stock/' + ticker + '/quote/avgTotalVolume' + \
          '?token=' + token
    print(url)
    response = requests.get(url)
    data = response.json()
    return data


def get_data_ticker_date_iex(ticker, date, token_type='Prod'):
    """
    Returns the intraday stock percent change for a ticker and date
    :param ticker:
    :param date: Date
    :param token_type: Prod or Sandbox
    :return: Dictionary of volume intraday percent change and max possible percent change
    """
    token = get_token_iex(token_type)
    api_response = get_daily_response_iex(ticker, date, token)
    if api_response.status_code == 200:
        data = api_response.json()
        open_price = data[0]['open']
        volume = data[0]['volume']
        close_price = data[0]['close']
        high_price = data[0]['high']
        low_price = data[0]['low']

        percent_change = (close_price - open_price) / open_price
        max_percent_change = (high_price - open_price) / open_price
        min_percent_change = (low_price - open_price) / open_price

        return {'open_price': open_price, 'close_price': close_price, 'volume': volume,
                'percent_change': percent_change, 'max_percent_change': max_percent_change,
                'min_percent_change': min_percent_change}


def get_next_trading_day_iex(date_object, token_type='Prod'):
    token = get_token_iex(token_type)

    # Subtract one day from date_object because the API returns the next day even if current day is a trade day
    date_object = date_object - datetime.timedelta(1)

    date_str = date_object.strftime('%Y%m%d')
    url = 'https://cloud.iexapis.com/stable/ref-data/us/dates/trade/next/1/' + date_str + \
          '?token=' + token
    api_response = requests.get(url)
    if api_response.status_code == 200:
        data = api_response.json()
        next_trade_date = data[0]['date']
        return next_trade_date
    else:
        return None


def get_company_info_iex(ticker, token_type='Prod'):
    token = get_token_iex(token_type)

    url = 'https://cloud.iexapis.com/stable/stock/' + ticker + '/company?token=' + token

    api_response = requests.get(url)
    if api_response.status_code == 200:
        data = api_response.json()
        tags = data['tags']
        country = data['country']
        employees = data['employees']
        primary_sic_code = data['primarySicCode']
        symbol = data['symbol']
        return {'ticker': symbol, 'tags': tags, 'country': country, 'employees': employees,
                'primary_sic_code': primary_sic_code}
    else:
        return None


def get_key_stats_iex(ticker, token_type='Prod'):
    token = get_token_iex(token_type)

    url = 'https://cloud.iexapis.com/stable/stock/' + ticker + '/stats?token=' + token

    api_response = requests.get(url)
    if api_response.status_code == 200:
        data = api_response.json()

        return data
    else:
        return None


def get_advanced_stats_iex(ticker, token_type='Prod'):
    token = get_token_iex(token_type)

    url = 'https://cloud.iexapis.com/stable/stock/' + ticker + '/advanced-stats?token=' + token

    api_response = requests.get(url)
    if api_response.status_code == 200:
        data = api_response.json()

        return data
    else:
        return None


def retrieve_ticker_from_name(name):
    """
    Attempts to find the ticker based on the company name (doesn't work great)
    :param name: Name of company
    :return: List of ticker, company name (for reference), exchange company is traded on, Flag if conlict
    """
    name = name.replace(' ', '%20')
    url = "https://www.marketwatch.com/tools/quotes/lookup.asp?siteID=mktw&Lookup=" + name + "&Country=us&Type=All"
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')

    tr = soup.find_all('tr')
    if len(tr) >= 2:  # Only return value if there is one listing in the table
        td = soup.find_all('td')
        ticker = td[0].text.strip()
        company_name = td[1].text.strip()
        exchange = td[2].text.strip()
        flag = ''
        if len(tr) > 2:
            # Add to flag to check if there was more than one result
            flag = 1
    else:
        ticker = company_name = exchange = flag = ""

    return [ticker, company_name, exchange, flag]


def get_trading_view_url(ticker_object):
    """
    Ticker symbol
    :param ticker_object: Ticker Object (ticker and exchange)
    :return: TradingView URL
    """
    ticker = ticker_object.ticker
    exchange = ticker_object.exchange

    url = 'https://www.tradingview.com/symbols/' + exchange + ':' + ticker
    return url


def date_article_reflected_in_stock(date_object):
    bell_close = datetime.datetime.strptime('16:00', '%H:%M').time()
    time = date_object.time()
    article_date = date_object.date()

    if time > bell_close:
        stock_date = article_date + datetime.timedelta(1)
    else:
        stock_date = article_date

    output = get_next_trading_day_iex(stock_date)

    return output

