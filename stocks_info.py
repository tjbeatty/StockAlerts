from bs4 import BeautifulSoup
import urllib.request
import requests
import datetime

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


def get_daily_response_iex(ticker, date, token='Prod'):
    """
    Gets daiy stock market data for a ticker/date
    :param ticker: Company ticker
    :param date: Date
    :param token: Token for iex
    :return: Response from API
    """
    date_object = datetime.date.today()
    if token.lower() == 'prod':
        token = 'pk_b7f4919ac9bc46499092ab5ad36a59e4'
    elif token.lower() == 'sandbox':
        token = 'Tpk_958d6bd4a69346e2bcbee47881694efa'

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


def get_average_volume(ticker):
    token = 'pk_b7f4919ac9bc46499092ab5ad36a59e4'
    url = 'https://cloud.iexapis.com/stable/stock/' + ticker + '/quote/avgTotalVolume' + \
          '?token=' + token
    print(url)
    response = requests.get(url)
    data = response.json()
    return data


def get_data_ticker_date_iex(ticker, date, token='Prod'):
    """
    Returns the intraday stock percent change for a ticker and date
    :param ticker:
    :param date: Date
    :param token: Token to access API
    :return: Dictionary of volume intraday percent change and max possible percent change
    """

    api_response = get_daily_response_iex(ticker, date, token)
    if api_response.status_code == 200:
        data = api_response.json()
        open_price = data[0]['open']
        volume = data[0]['volume']
        close_price = data[0]['close']
        high_price = data[0]['high']

        percent_change = (close_price - open_price) / open_price
        max_percent_change = (high_price - open_price) / open_price

        return {'open_price': open_price, 'close_price': close_price, 'volume': volume,
                'percent_change': percent_change, 'max_percent_change': max_percent_change}


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


# print(get_percent_change_from_date_iex('TSLA', '02/02/2021'))

# tickers = get_ticker_from_description('SAN DIEGO, CA, April  14, 2021  (GLOBE NEWSWIRE) -- GreenBox (POS NASDAQ: GBOX) ("GreenBox" or "the Company"), an emerging financial technology company leveraging proprietary blockchain security to build customized payment solutions, today announced the company has selected Signature Bank (Nasdaq: SBNY), a New York-based, full-service commercial bank, as the banking solution to meet its smart-contract token infrastructure needs.')
#
# for ticker in tickers:
#     print(ticker.ticker)