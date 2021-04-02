import slack
from business_wire import *
from mysql_functions import *


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


def send_alert_to_slack(alert):
    client = slack.WebClient(token='xoxb-181014212021-1852663037783-J5QEPYmiqQwGtfeTi6oe73PZ')
    client.chat_postMessage(channel='business-wire-alerts', type='mrkdwn', text=alert)


def execute_alert_system(url, keywords, mysql_table):
    matched_stories = filter_bus_wire_rss_news_feed_with_keyword(url, keywords)
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

        if not check_table_for_story(ticker, date, title, mysql_table):
            formatted_alert = format_business_wire_alert_for_slack(story)
            send_alert_to_slack(formatted_alert)
            # print(ticker, date, title, description, date_time, keywords)
            add_story_to_table(ticker, date, title, description, date_time, keyword_matched, mysql_table)
            print("Sent " + ticker + " story from " + date_time + " to Slack")
            alerts_sent += 1
            tickers.append(ticker)
        # else:
        #     print(str(check_table_for_story(ticker, date, title, mysql_table)) + " already found in table")

    tickers = '^'.join(tickers)
    log_rss_ping(match_count, alerts_sent, tickers, 'marketwatch_pings')


fda_phrases = ['FDA', 'Phase 0', 'Phase 1', 'Phase 2', 'Phase 3', 'Phase I', 'Phase II', 'Phase III']
execute_alert_system('https://feed.businesswire.com/rss/home/?rss=G1QFDERJXkJeEVlZWA==', fda_phrases,
                     'marketwatch_alerts')
