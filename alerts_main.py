import slack
from business_wire import *
from mysql_functions import *
from globe_newswire import *
import csv


def import_keywords(file_in):
    """
    Takes aa file of keywords and converts it to a list
    :param file_in: File of keywords to search an article for, one per line
    :return: List of keywords
    """
    keywords = []

    my_path = os.path.abspath(os.path.dirname(__file__))  # Finds the path of this file
    filepath = my_path + "/" + file_in
    with open(filepath, 'r') as csv_in:
        csv_reader = csv.reader(csv_in)
        header_throwaway = next(csv_reader)  # Header row of file not to be included in list
        for row in csv_reader:
            keywords.append(row[0])

    return keywords


def check_table_for_story(url, table_name):
    """
    Checks a MySQL table for an article
    :param url: URL of the article
    :param table_name: Table of articles to be searched
    :return: Result (if article found) or None (if no article found)
    """
    connection = create_db_connection()
    query = 'SELECT url ' \
            'FROM ' + table_name + \
            ' WHERE url = "' + url + '"'

    # print(query)
    result = read_query(connection, query)

    # Will return NONE value if there is no data
    return result


def add_story_to_table(story_object, keyword_matched, table_name):
    """
    Adds a story to a MySQL table
    :param story_object: Article object
    :param table_name: Table of articles to be searched
    :return: Nothing
    """
    title = story_object.title
    date_time_et_obj = story_object.date_time
    date = date_time_et_obj.strftime('%Y-%m-%d')
    date_time = date_time_et_obj.strftime('%Y-%m-%d %H:%M:%S')
    ticker_object_list = story_object.ticker_object_list
    description = story_object.description
    source = story_object.source
    link = story_object.url
    exchange_ticker_list = [ticker.exchange + ': ' + ticker.ticker for ticker in ticker_object_list]
    tickers_in_story = '^'.join(exchange_ticker_list)

    connection = create_db_connection()
    query = 'INSERT INTO ' + table_name + \
            ' (ticker, date, title, description, date_time_story_et, keyword_hit, source, url) ' \
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
    values = (tickers_in_story, date, title, description, date_time, keyword_matched, source, link)

    execute_placeholder_query(connection, query, values)


def log_rss_ping(matched_stories, alerts_sent, tickers, url, table_name):
    """
    Logs a successful RSS ping to a table (used to check that the job is running on cron)
    :param matched_stories: Number of stories matched for ping
    :param alerts_sent: Number of alerts sent to Slack
    :param tickers: Tickers of companies in the alerts
    :param url: url of RSS feed
    :param table_name: Table to log the ping
    :return: Nothing
    """
    connection = create_db_connection()
    date_time = datetime.datetime.now()
    query = 'INSERT INTO ' + table_name + \
            ' (date_time, matched_stories, alerts_sent, tickers, rss_url) VALUES (%s, %s, %s, %s, %s)'
    values = (date_time, matched_stories, alerts_sent, tickers, url)

    execute_placeholder_query(connection, query, values)


def format_alert_for_slack(entry):
    """
    Formats an alert for Slack
    :param entry: A news article object
    :return: Formatted text for Slack alert
    """

    title = entry.title
    description = entry.description
    date_time_et = entry.date_time
    date_time = date_time_et.strftime('%m/%d/%y %-I:%M %p %Z')
    link = entry.url
    ticker_object_list = entry.ticker_object_list
    source = entry.source
    exchange_ticker_list = [ticker.exchange + ': ' + ticker.ticker for ticker in ticker_object_list]
    trading_view_urls = [get_trading_view_url(ticker) for ticker in ticker_object_list]

    text = '<!here> \n'
    text += '*Date/Time:* `' + date_time + '`\n'
    text += '*Source:* ' + source + '\n'
    text += '*Ticker:* ' + ', '.join(exchange_ticker_list) + '\n'
    for url in trading_view_urls:
        text += '*TV Link:* ' + url + '\n'
    text += '*Title:* `' + title + '`\n'
    text += '*Description:* ```' + description + '```\n'
    text += '*News Link:* ' + link

    return text


def send_alert_to_slack(alert):
    """
    Sends an alert to a Slack channel with formatted text
    :param alert: Formatted text for Slack alert
    :return: Nothing
    """
    client = slack.WebClient(token='')
    client.chat_postMessage(channel='business-wire-alerts', type='mrkdwn', text=alert)


def filter_rss_news_feed_with_keyword(url, keywords):
    """
    Takes an RSS feed and finds articles with keywords
    :param url: url of RSS feed
    :param keywords: keyword or sequential words ("word or words"),
    or a list of keywords to search news story against (["word or words 1", "word or words 2"...])
    :return: list of article objects
    """
    if 'businesswire' in url:
        news_stories = ping_bus_wire_rss_news_feed(url)
    elif 'globenewswire' in url:
        news_stories = ping_gnw_rss_news_feed(url)
    else:
        news_stories = []

    output = []
    for entry in news_stories:
        description = entry.description
        ticker_object = entry.ticker_object_list
        if ticker_object:
            if type(keywords) == list:
                for keyword in keywords:
                    if keyword.lower() in description.lower():
                        output.append({'article': entry, 'keyword': keyword})
            elif type(keywords) == str:
                if keywords.lower() in description.lower():
                    output.append({'article': entry, 'keyword': keywords})

    return output


# TODO - Add method to write to another table for "urls checked", to be used in conjunction with searching the article
#  for the tickers instead of just the short description

# TODO - check actual article for ticker(s) and keywords/sentiment.
#  - Log each article/url in a MySQL table has having been checked (so we don't waste time going into article again).
#  -
def execute_alert_system(rss_url, keywords, mysql_table):
    """
    Main method. Executes the alert system
    :param rss_url: url of RSS feed
    :param keywords: Keywords to search articles for
    :param mysql_table: MySQL table to write found article results to
    :return: Nothing
    """
    matched_stories = filter_rss_news_feed_with_keyword(rss_url, keywords)
    match_count = len(matched_stories)
    alerts_sent = 0
    tickers_logged_rss_ping = []

    for story_keyword in matched_stories:
        story = story_keyword['article']
        keyword_matched = story_keyword['keyword']
        date_time = story.date_time.strftime('%Y-%m-%d %H:%M:%S')
        ticker_object_list = story.ticker_object_list
        link = story.url
        exchange_ticker_list = [ticker.exchange + ': ' + ticker.ticker for ticker in ticker_object_list]
        tickers_in_story = '^'.join(exchange_ticker_list)

        if not check_table_for_story(link, mysql_table):
            formatted_alert = format_alert_for_slack(story)
            send_alert_to_slack(formatted_alert)
            add_story_to_table(story, keyword_matched, mysql_table)
            print("Sent " + tickers_in_story + " story from " + date_time + " to Slack")
            alerts_sent += 1
            tickers_logged_rss_ping.append(tickers_in_story)

    tickers_logged_rss_ping = '^'.join(tickers_logged_rss_ping)
    log_rss_ping(match_count, alerts_sent, tickers_logged_rss_ping, rss_url, 'rss_pings')


keywords = import_keywords('csvs/keywords.csv')
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

# print(ping_bus_wire_rss_news_feed(bw_health_rss))