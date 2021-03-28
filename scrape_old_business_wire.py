from selenium.webdriver.common.by import By
import csv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import business_wire
import datetime
import stocks_info
from time import sleep
from stocks_info import normalize_date_return_object


def convert_text_date_for_api(date_string):
    date_object = datetime.datetime.strptime(date_string, '%B %d, %Y')
    date_out = date_object.strftime('%m/%d/%Y')
    return date_out


def initialize_browser():
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    browser = webdriver.Chrome(options=options)
    return browser


def is_english_story(url):
    if '/en/' in url:
        return True
    else:
        return False


def get_stories_from_search_page(url, browser):
    browser.get(url)
    timeout = 20

    try:
        # Wait until the bottom image element loads before reading in data.
        WebDriverWait(browser, timeout). \
            until(EC.visibility_of_element_located((By.XPATH, '//*[@id="bw-group-all"]/div/div/div[3]/'
                                                              'section/ul/li[last()]/p')))
        # Retrieve dates, title, desciption, url from each story
        date_elems = browser.find_elements_by_xpath('//*[@id="bw-group-all"]/div/div/div[3]/section/'
                                                    'ul/li[*]/div[1]/time')
        title_elems = browser.find_elements_by_xpath('//*[@id="bw-group-all"]/div/div/div[3]/section/ul/li[*]/h3/a')
        heading_elems = browser.find_elements_by_xpath('//*[@id="bw-group-all"]/div/div/div[3]/section/ul/li[*]/p')
        url_elems = browser.find_elements_by_xpath('//*[@id="bw-group-all"]/div/div/div[3]/section/ul/li[*]/h3/a')

        # Take text from each object an dput in lists
        date_text = [elem.text for elem in date_elems]
        title_text = [elem.text for elem in title_elems]
        heading_text = [elem.text for elem in heading_elems]
        urls = [elem.get_attribute('href') for elem in url_elems]

        output = []
        for i, n in enumerate(urls):
            ticker = business_wire.find_ticker_in_description(heading_text[i])
            if is_english_story(urls[i]) and ticker:
                date = convert_text_date_for_api(date_text[i])
                article_object = business_wire.BusinessWireArticle(date_text[i], date, title_text[i], ticker,
                                                                   heading_text[i], urls[i])
                output.append(article_object)

        return output
    except TimeoutException:
        return []


def old_bus_wire_news_from_search_term(search_term, pages):
    browser = initialize_browser()

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

        search_page_details = get_stories_from_search_page(url, browser)
        with open(csv_name, 'a+') as csvout:
            for story in search_page_details:
                date_text = story.date_text
                date = story.date
                ticker = story.ticker
                title_text = story.title
                heading_text = story.description
                url = story.url

                output = [date, ticker, title_text, heading_text, url]
                csv_writer = csv.writer(csvout)
                csv_writer.writerow(output)

    browser.quit()


def find_min_date_on_page(url, browser):
    browser.get(url)
    timeout = 20

# TODO Make sure this works
    try:
        # Wait until the bottom image element loads before reading in data.
        WebDriverWait(browser, timeout). \
            until(EC.visibility_of_element_located((By.XPATH, '//*[@id="bw-group-all"]/div/div/div[3]/'
                                                              'section/ul/li[last()]/p')))
        # Retrieve min date from page
        min_date_text = browser.find_elements_by_xpath('//*[@id="bw-group-all"]/div/div/div[3]/section/'
                                                       'ul/li[last()]/div[1]/time')

        min_date = normalize_date_return_object(min_date_text)

        return min_date
    except TimeoutException:
        return ''


# TODO still need to implement this
def find_story_from_ticker_date(ticker, date_string):
    browser = initialize_browser()

    min_date_on_page = datetime.datetime.today()
    date_object_of_event = normalize_date_return_object(date_string)
    url_page = 1
    while min_date_on_page > date_object_of_event:
        url = 'https://www.businesswire.com/portal/site/home/search/?searchType=news&searchTerm=' \
              + ticker + '&searchPage=' + str(url_page)
        min_date_on_page = find_min_date_on_page(url)

        page_details = get_stories_from_search_page(url, browser)
        browser.find_elements_by_xpath('//*[@id="bw-group-all"]/div/div/div[3]/section/'
                                       'ul/li[*]/div[1]/time')
        url_page += 1


def pull_daily_change_for_all_bus_wire_articles(csv_input, csv_output):
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
                ticker = business_wire.find_ticker_in_description(description)
                if ticker:
                    date_str = convert_text_date_for_api(date)
                    stock_day_data = stocks_info.get_percent_change_from_date_iex(ticker, date_str)
                    if stock_day_data:
                        volume = stock_day_data['volume']
                        percent_change = stock_day_data['percent_change']
                        max_percent_change = stock_day_data['max_percent_change']
                        row.extend([percent_change, max_percent_change, volume])
                        csv_writer.writerow(row)


# retrieve_old_bus_wire_news('FDA', 2000)
# pull_daily_change_for_all_bus_wire_articles('fda_test.csv')


# pull_daily_change_for_all_bus_wire_articles('FDA_check.csv',
#                                             'FDA_percent_change2.csv')


# browser = initialize_browser()
# print(get_stories_from_search_page('https://www.businesswire.com/portal/site/home/template.PAGE/search/?searchType=news&searchTerm=FDA&searchPage=1', browser))

old_bus_wire_news_from_search_term('FDA', 1)