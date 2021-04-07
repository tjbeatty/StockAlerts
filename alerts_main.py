import slack
from business_wire import *
from mysql_functions import *
from globe_newswire import *
import csv


def import_keywords(file_in):
    keywords = []
    with open(file_in, 'r') as csv_in:
        csv_reader = csv.reader(csv_in)
        header_throwaway = next(csv_reader)
        for row in csv_reader:
            keywords.append(row[0])

    return keywords


def check_table_for_story(ticker, date, title, source, table_name):
    connection = create_db_connection()
    query = 'SELECT ticker, date_time_story_et, source ' \
            'FROM ' + table_name + \
            ' WHERE ticker = "' + ticker + '" AND date = "' + date + '" AND title = "' + title + \
            '" AND source = "' + source + '"'

    # print(query)
    result = read_query(connection, query)

    # Will return NONE value if there is no data
    return result


def add_story_to_table(ticker, date, title, description, date_time, keyword, source, table_name):
    connection = create_db_connection()
    query = 'INSERT INTO ' + table_name + \
            ' (ticker, date, title, description, date_time_story_et, keyword_hit, source) ' \
            'VALUES (%s, %s, %s, %s, %s, %s, %s)'
    values = (ticker, date, title, description, date_time, keyword, source)

    execute_placeholder_query(connection, query, values)


def log_rss_ping(matched_stories, alerts_sent, tickers, table_name):
    connection = create_db_connection()
    date_time = datetime.datetime.now()
    query = 'INSERT INTO ' + table_name + \
            ' (date_time, matched_stories, alerts_sent, tickers) VALUES (%s, %s, %s, %s)'
    values = (date_time, matched_stories, alerts_sent, tickers)

    execute_placeholder_query(connection, query, values)


def format_alert_for_slack(entry):
    title = entry['title']
    description = entry['description']
    date_time = entry['date_time']
    link = entry['link']
    ticker = entry['ticker']
    source = entry['source']
    trading_view_url = get_trading_view_url(ticker)

    text = '<!here> \n'
    text += '*Date/Time:* `' + date_time + '`\n'
    text += '*Source:* ' + source + '\n'
    text += '*Ticker:* ' + ticker + '\n'
    text += '*Title:* `' + title + '`\n'
    text += '*Description:* ```' + description + '```\n'
    text += '*News Link:* ' + link + '\n'
    text += '*TV Link:* ' + trading_view_url

    return text


def send_alert_to_slack(alert):
    client = slack.WebClient(token='xoxb-181014212021-1852663037783-J5QEPYmiqQwGtfeTi6oe73PZ')
    client.chat_postMessage(channel='business-wire-alerts', type='mrkdwn', text=alert)


def filter_rss_news_feed_with_keyword(url, keywords):
    """
    :param url: rss url to ping
    :param keywords: keyword or sequential words ("word or words"),
    or a list of keywords or sequential to search news story against (["word or words 1, "word or words 2"...])
    :return: dictionary containing ticker, title, article description, datetime or article (PT), link to article, date,
    datetime or article (exchange time)
    """
    if 'businesswire' in url:
        news_stories = ping_bus_wire_rss_news_feed(url)
    elif 'globenewswire' in url:
        news_stories = ping_gnw_rss_news_feed(url)
    else:
        news_stories = []

    output = []
    for entry in news_stories:
        description = entry['description']
        ticker = get_ticker_from_description(description)
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


def execute_alert_system(url, keywords, mysql_table):
    matched_stories = filter_rss_news_feed_with_keyword(url, keywords)
    match_count = len(matched_stories)
    alerts_sent = 0
    tickers = []

    for story in matched_stories:
        title = story['title']
        date = story['date']
        date_time = story['date_time_sql']
        ticker = story['ticker']
        description = story['description']
        keyword_matched = story['keyword_matched']
        source = story['source']

        if not check_table_for_story(ticker, date, title, source, mysql_table):
            formatted_alert = format_alert_for_slack(story)
            send_alert_to_slack(formatted_alert)
            # print(ticker, date, title, description, date_time, keywords)
            add_story_to_table(ticker, date, title, description, date_time, keyword_matched, source, mysql_table)
            print("Sent " + ticker + " story from " + date_time + " to Slack")
            alerts_sent += 1
            tickers.append(ticker)
        # else:
        #     print(str(check_table_for_story(ticker, date, title, mysql_table)) + " already found in table")

    tickers = '^'.join(tickers)
    log_rss_ping(match_count, alerts_sent, tickers, 'rss_pings')


keywords = import_keywords('keywords.csv')
fda_phrases = ['FDA', 'Phase 0', 'Phase 1', 'Phase 2', 'Phase 3', 'Phase I', 'Phase II', 'Phase III']
financial_words = ['sales results', 'financials', 'letter to stakeholders', 'provides update', 'business update',
                   'financial results']

gnw_public_company_rss = 'https://www.globenewswire.com/RssFeed/orgclass/1/feedTitle/GlobeNewswire%20-%20' \
                         'News%20about%20Public%20Companies'
bw_tech_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEFpQWg=='
bw_health_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEVlZWA=='
bw_energy_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEFpQXw=='
bw_defense_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeGVpZWQ=='
bw_science_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeGVtXWQ=='
bw_auto_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEVlZXw=='
bw_comms_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEFpRVQ=='
bw_construction_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEFpRVA=='
bw_manufacturing_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEFpTXA=='
bw_public_policy_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEFpQWQ=='
bw_retail_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEF5XWQ=='
bw_trade_show_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEFxXVA=='
bw_transport_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEFpQVQ=='
bw_travel_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEVlZWQ=='
bw_vc_rss = 'https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJdEVhZXw=='


rss_feeds = [gnw_public_company_rss, bw_tech_rss, bw_energy_rss, bw_defense_rss, bw_health_rss, bw_science_rss,
             bw_auto_rss, bw_comms_rss, bw_construction_rss, bw_manufacturing_rss, bw_public_policy_rss, bw_retail_rss,
             bw_trade_show_rss, bw_transport_rss, bw_travel_rss, bw_vc_rss]

for feed in rss_feeds:
    execute_alert_system(feed, keywords, 'story_alerts')
