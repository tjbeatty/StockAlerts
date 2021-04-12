from selenium.webdriver.common.by import By
import csv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import business_wire
from business_wire import find_story_from_ticker_date
import datetime
import stocks_info
from time import sleep
from stocks_info import normalize_date_return_object
from stocks_info import get_ticker_from_description


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
                ticker_objects = get_ticker_from_description(description)
                if ticker_objects:
                    date_str = stocks_info.convert_text_date_for_api(date)
                    for ticker_object in ticker_objects:
                        ticker = ticker_object.ticker
                        stock_day_data = stocks_info.get_percent_change_from_date_iex(ticker, date_str)
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

    browser = business_wire.initialize_browser()
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


def old_bus_wire_news_from_search_term(search_term, pages):
    """
    Pull all BusinessWire news related to a search term, up to a certain number of pages
    :param search_term: Search term
    :param pages: Number of result pages to retrieve articles from
    :return: Outputs a CSV of all the articles
    """
    browser = business_wire.initialize_browser()

    # Initialize the file output (write the header)
    header = ['date', 'ticker', 'title', 'description', 'url']
    csv_name = search_term + '_historical_business_wire_stories.csv'

    # Remove file if it already exists
    if os.path.exists(csv_name):
        os.remove(csv_name)

    with open(csv_name, 'w') as csvout:
        csv_writer = csv.writer(csvout)
        csv_writer.writerow(header)

    for page in range(1, pages+1):
        print("Now on page #" + str(page) + "...")
        url = 'https://www.businesswire.com/portal/site/home/search/?searchType=news&searchTerm=' \
              + search_term + '&searchPage=' + str(page)

        search_page_details = business_wire.get_stories_from_search_page(url, browser)
        with open(csv_name, 'a+') as csvout:
            for story in search_page_details:
                date = story.date
                ticker = story.ticker
                title_text = story.title
                heading_text = story.description
                url = story.url

                output = [date, ticker, title_text, heading_text, url]
                csv_writer = csv.writer(csvout)
                csv_writer.writerow(output)

    browser.quit()



# find_story_from_ticker_date('AVEO', '3/10/2021', browser=business_wire.initialize_browser())