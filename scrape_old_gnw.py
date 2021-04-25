import csv
import os
from globe_newswire import find_story_from_ticker_two_days, get_stories_from_search_page, initialize_browser
from stocks_info import get_ticker_objects_from_description, convert_text_date_for_api


# TODO - Get rid of this entire method. Have an identical one in scrape old bw
def pull_daily_change_for_all_gnw_articles(csv_input, csv_output):
    """
    Pull daily stock change for all articles referenced in a csv
    :param csv_input: Name of input CSV
    :param csv_output: Name of output CSV
    :return: Nothing
    """
    header = ['date', 'title', 'description', 'percent_change', 'max_percent_change', 'volume']
    output = []
    with open(csv_input, 'r') as csv_in:
        csv_reader = csv.reader(csv_in)
        header_throwaway = next(csv_reader)
        with open(csv_output, 'w') as csv_out:
            csv_writer = csv.writer(csv_out)
            csv_writer.writerow(header)

            for row in csv_reader:
                [date, title, description] = row
                ticker_objects = get_ticker_objects_from_description(description)
                if ticker_objects:
                    date_str = convert_text_date_for_api(date)
                    for ticker_object in ticker_objects:
                        ticker = ticker_object.ticker
                        stock_day_data = get_ticker_objects_from_description(ticker, date_str)
                        if stock_day_data:
                            volume = stock_day_data['volume']
                            percent_change = stock_day_data['percent_change']
                            max_percent_change = stock_day_data['max_percent_change']
                            row.extend([percent_change, max_percent_change, volume])
                            csv_writer.writerow(row)


def pull_gnw_stories_ticker_date(csv_input, csv_output):
    """
    Pull all stories that might relate to a ticker/date event from an input CSV
    :param csv_input: Name of input CSV
    :param csv_output: Name of output CSV
    :return: Nothing
    """
    header = ['date', 'ticker', 'pct_change_prev_close', 'day_percent_change',
              'max_day_percent_change', 'title', 'description', 'url', 'same_or_prev']
    output = []

    browser = initialize_browser()
    with open(csv_input, 'r') as csv_in:
        csv_reader = csv.reader(csv_in)
        header_throwaway = next(csv_reader)

        with open(csv_output, 'w') as csv_out:
            csv_writer = csv.writer(csv_out)
            csv_writer.writerow(header)

            for row in csv_reader:
                [date, exchange, ticker, pct_change_previous_close, volume,
                 day_percent_change, max_day_percent_change] = row

                date = date.replace(' ', '')
                exchange = exchange.replace(' ', '')
                ticker = ticker.replace(' ', '')

                if exchange.lower().replace(' ', '') == 'xnas':
                    exchange_long = 'nasdaq'
                elif exchange.lower().replace(' ', '') == 'xnys':
                    exchange_long = 'nyse'

                print(date, ticker)

                stories = find_story_from_ticker_two_days(ticker, date, browser, exchange_long)
                same_day_stories = stories['same_day_stories']
                for story in same_day_stories:
                    title = story.title
                    description = story.description
                    url = story.url
                    same_or_prev = 'same'
                    row_out = [date, ticker, pct_change_previous_close, day_percent_change,
                               max_day_percent_change, title, description, url, same_or_prev]
                    csv_writer.writerow(row_out)

                prev_day_stories = stories['prev_day_stories']
                for story in prev_day_stories:
                    title = story.title
                    description = story.description
                    url = story.url
                    same_or_prev = 'prev'
                    row_out = [date, ticker, pct_change_previous_close, day_percent_change,
                               max_day_percent_change, title, description, url, same_or_prev]
                    csv_writer.writerow(row_out)


def old_gnw_news_from_search_term(search_term, num_articles, browser, page_start=1):
    """
    Finds older GlobeNewseire articles that are related to a search term
    :param search_term: Search term
    :param num_articles: Number of article to retrieve
    :param browser: The initialized Selinium browser
    :param page_start: The search page to start on (in case
    :return: Outputs a list of
    """
    articles_retrieved = 0
    page = page_start
    output = []
    try:
        while articles_retrieved < num_articles:
            print("Found " + articles_retrieved + " articles...")
            url = 'https://www.globenewswire.com/search/lang/en/exchange/nyse,nasdaq/keyword/' \
                  + search_term + '?page=' + str(page)

            articles_found = get_stories_from_search_page(url, browser)

            page = page + 1
            articles_retrieved = articles_retrieved + 1

            for story in articles_found:
                output.append(story)

            return output
    except:
        return output


# pull_gnw_stories_ticker_date('daily_stocks_20perc_loss.csv', 'daily_stocks_20perc_loss_gnw_stories.csv')