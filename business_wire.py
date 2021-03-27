import feedparser
from pytz import timezone
from stocks_info import *
from mysql_functions import *
import re
import lxml
import html5lib
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time


def find_ticker_in_description(description):
    ticker = False
    if '(nasdaq:' in description.lower() or '(nyse:' in description.lower() \
            or bool(re.search('\$[a-z]', description.lower())):
        if '(nasdaq:' in description.lower() or '(nyse:' in description.lower():
            ticker = description.split(':')[1].split(')')[0].replace(' ', '')
        else:
            ticker = description.split('$')[1].split()[0].replace(' ', '')
    else:
        ticker = False

    return ticker


def ping_bus_wire_rss_news_feed(url):
    feed = feedparser.parse(url)
    output = []
    for entry in feed.entries:
        description = entry.description
        ticker = find_ticker_in_description(description)

        if ticker:
            date_time_utc = entry.published + 'C'
            date_time_utc_object = datetime.datetime.strptime(date_time_utc, '%a, %d %b %Y %H:%M:%S %Z') \
                .replace(tzinfo=timezone('UTC'))
            date_time_eastern_object = date_time_utc_object.astimezone(timezone('US/Eastern'))
            date_time_sql = date_time_eastern_object.strftime('%Y-%m-%d %H:%M:%S')
            date_time_pt_object = date_time_utc_object.astimezone(timezone('US/Pacific'))
            date_time_pt = date_time_pt_object.strftime('%m/%d/%y %-I:%M %p %Z')
            date = date_time_pt_object.strftime('%Y-%m-%d')

            title = entry.title
            link = entry.link
            output.append({'ticker': ticker, 'title': title, 'description': description, 'date_time': date_time_pt,
                           'link': link, 'date': date, 'date_time_sql': date_time_sql})

    return output


def filter_bus_wire_rss_news_feed_with_keyword(url, keywords):
    """
    :param url: rss url to ping
    :param keywords: keyword or sequential words ("word or words"),
    or a list of keywords or sequential to search news story against (["word or words 1, "word or words 2"...])
    :return: dictionary containing ticker, title, article description, datetime or article (PT), link to article, date,
    datetime or article (exchange time)
    """

    news_stories = ping_bus_wire_rss_news_feed(url)
    output = []
    for entry in news_stories:
        description = entry['description']
        ticker = find_ticker_in_description(description)
        if ticker:
            if type(keywords) == list:
                for keyword in keywords:
                    if keyword in description:
                        entry['keyword_matched'] = keyword
                        output.append(entry)
            elif type(keywords) == str:
                if keywords in description:
                    entry['keyword_matched'] = keywords
                    output.append(entry)

    return output


def filter_bus_wire_news_feed_with_nonsequential_keywords(url, keywords):
    news_stories = ping_bus_wire_rss_news_feed(url)
    output = []
    for entry in news_stories:
        description = entry['description']
        ticker = find_ticker_in_description(description)
        if ticker:
            for keyword in keywords:
                if keyword in description and keyword == keywords[-1]:
                    output.append(entry)
                else:
                    # If any of the keywords do not match, go to next news story
                    break

    return output


def format_business_wire_alert_for_slack(entry):
    title = entry['title']
    description = entry['description']
    date_time = entry['date_time']
    link = entry['link']
    ticker = entry['ticker']
    trading_view_url = get_trading_view_url(ticker)

    text = '<!here> \n'
    text += '*Date/Time:* `' + date_time + '`\n'
    text += '*Title:* `' + title + '`\n'
    text += '*Ticker:* ' + ticker + '\n'
    text += '*Description:* ```' + description + '```\n'
    text += '*News Link:* ' + link + '\n'
    text += '*TV Link:* ' + trading_view_url

    return text


def check_table_for_story(ticker, date, title, table_name):
    connection = create_db_connection()
    query = 'SELECT ticker, date_time_story_et ' \
            'FROM ' + table_name + \
            ' WHERE ticker = "' + ticker + '" AND date = "' + date + '" AND title = "' + title + '"'

    # print(query)
    result = read_query(connection, query)

    # Will return NONE value if there is no data
    return result


def add_story_to_table(ticker, date, title, description, date_time, keyword, table_name):
    connection = create_db_connection()
    query = 'INSERT INTO ' + table_name + \
            ' (ticker, date, title, description, date_time_story_et, keyword_hit) VALUES (%s, %s, %s, %s, %s, %s)'
    values = (ticker, date, title, description, date_time, keyword)

    execute_placeholder_query(connection, query, values)


def log_rss_ping(matched_stories, alerts_sent, tickers, table_name):
    connection = create_db_connection()
    date_time = datetime.datetime.now()
    query = 'INSERT INTO ' + table_name + \
            ' (date_time, matched_stories, alerts_sent, tickers) VALUES (%s, %s, %s, %s)'
    values = (date_time, matched_stories, alerts_sent, tickers)

    execute_placeholder_query(connection, query, values)



