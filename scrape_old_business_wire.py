import csv
import os
from business_wire import find_story_from_ticker_date, get_stories_from_search_page, initialize_browser
from stocks_info import convert_text_date_for_api, get_data_ticker_date_iex
from general_functions import get_ticker_objects_from_description


def pull_daily_change_for_all_bus_wire_articles(csv_input, csv_output):
    """
    Pull stock market data for all ticker/date combos in a file and return a file with that data
    :param csv_input: Input csv name
    :param csv_output: Output csv name
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
                        stock_day_data = get_data_ticker_date_iex(ticker, date_str)
                        if stock_day_data:
                            volume = stock_day_data['volume']
                            percent_change = stock_day_data['percent_change']
                            max_percent_change = stock_day_data['max_percent_change']
                            row.extend([percent_change, max_percent_change, volume])
                            csv_writer.writerow(row)


def pull_bus_wire_news_stories_ticker_date(csv_input, csv_output):
    """
    Pull all articles from BusinessWire associated with a stock ticker on a specific date
    :param csv_input: CSV Input name
    :param csv_output: CSV Output name
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
                print(date, ticker)

                stories = find_story_from_ticker_date(ticker, date, browser)
                print(stories)
                same_day_stories = stories['same_day_stories']
                for story in same_day_stories:
                    title = story.title
                    print(title)
                    description = story.description
                    url = story.url
                    same_or_prev = 'same'
                    row_out = [date, ticker, pct_change_previous_close, day_percent_change,
                               max_day_percent_change, title, description, url, same_or_prev]
                    csv_writer.writerow(row_out)

                prev_day_stories = stories['prev_day_stories']
                for story in prev_day_stories:
                    title = story.title
                    print(title)
                    description = story.description
                    url = story.url
                    same_or_prev = 'prev'
                    row_out = [date, ticker, pct_change_previous_close, day_percent_change,
                               max_day_percent_change, title, description, url, same_or_prev]
                    csv_writer.writerow(row_out)


def old_bus_wire_news_from_search_term(search_term, num_articles, browser, page_start=1):
    """
    Pull all BusinessWire news related to a search term, up to a certain number of articles
    :param search_term: Search term
    :param num_articles: Number of article to retrieve
    :param browser: The initialized Selinium browser
    :param page_start: The search page to start on (in case
    :return: Outputs a CSV of all the articles
    """

    articles_retrieved = 0
    page = page_start
    output = []
    try:
        while articles_retrieved < num_articles:
            print("Found " + articles_retrieved + " articles...")
            url = 'https://www.businesswire.com/portal/site/home/search/?searchType=news&searchTerm=' \
                  + search_term + '&searchPage=' + str(page)

            articles_found = get_stories_from_search_page(url, browser)

            page = page + 1
            articles_retrieved = articles_retrieved + 1

            for story in articles_found:
                output.append(story)

            return output
    except:
        return output



# find_story_from_ticker_date('AVEO', '3/10/2021', browser=business_wire.initialize_browser())