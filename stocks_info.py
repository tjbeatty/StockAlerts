from bs4 import BeautifulSoup
import urllib.request
import requests
import datetime
import re
from iexfinance.stocks import get_historical_data
import iexfinance

# TODO - Determine how to make it find the FIRST ticker in the description, regardless of exchange
def get_ticker_from_description(description):
    ticker = False
    first_split = ''
    if 'nasdaq:' in description.lower():
        first_split = description.lower().split('nasdaq:')[1]
    elif 'nyse:' in description.lower():
        first_split = description.lower().split('nyse:')[1]
    elif 'nasdaqgs:' in description.lower():
        first_split = description.lower().split('nasdaqgs:')[1]
    elif bool(re.search('\$[a-z]', description.lower())):
        first_split = description.lower().split('$')[1].split()[0].replace(' ', '')
    else:
        ticker = False

    if first_split != '':
        replace_spaces = first_split.replace(' ', '')
        ticker = re.split('[^a-z]', replace_spaces)[0].upper()
    return ticker


def normalize_date_return_object(date_string):
    months_list = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                   'November', 'December']
    short_months_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    timezones = ['ET', 'CT', 'MT', 'PT', 'EDT', 'CDT', 'MDT', 'PDT', 'EST', 'CST', 'MST', 'PST']
    month_text_in_date = [ele for ele in months_list if (ele in date_string)]
    short_month_text_in_date = [ele for ele in short_months_list if (ele in date_string)]
    timezone_text_in_date = [ele for ele in timezones if (ele in date_string)]
    if month_text_in_date and "," in date_string:
        if ':' in date_string:
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


def convert_text_date_for_api(date_string):
    date_object = datetime.datetime.strptime(date_string, '%B %d, %Y')
    date_out = date_object.strftime('%m/%d/%Y')
    return date_out


def get_daily_response_polygon(ticker, date):
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


def get_percent_change_from_date_iex(ticker, date, token='Prod'):

    api_response = get_daily_response_iex(ticker, date, token)
    if api_response.status_code == 200:
        data = api_response.json()
        open_price = data[0]['open']
        volume = data[0]['volume']
        close_price = data[0]['close']
        high_price = data[0]['high']

        percent_change = (close_price - open_price) / open_price
        max_percent_change = (high_price - open_price) / open_price

        return {'volume': volume, 'percent_change': percent_change, 'max_percent_change': max_percent_change}


def retrieve_ticker_from_name(name):
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


def get_trading_view_url(ticker):
    url = 'https://www.tradingview.com/symbols/' + ticker
    return url


# print(get_percent_change_from_date_iex('TSLA', '02/02/2021'))
