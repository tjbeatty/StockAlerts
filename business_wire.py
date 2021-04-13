import feedparser
from pytz import timezone
from stocks_info import *
import re
from selenium.webdriver.common.by import By
import csv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import os
import datetime
from stocks_info import normalize_date_return_object
from stocks_info import get_ticker_from_description
from stock_alert_classes import NewsArticle


def ping_bus_wire_rss_news_feed(url):
    """
    Pull all articles from the RSS feed that have a stock ticker in the article
    :param url: url of RSS Feed
    :return: List of article objects
    """
    feed = feedparser.parse(url)
    output = []
    for entry in feed.entries:
        description = entry.description
        ticker_object = get_ticker_from_description(description)

        if ticker_object:
            date_time_utc = entry.published + 'C'
            date_time_utc_object = datetime.datetime.strptime(date_time_utc, '%a, %d %b %Y %H:%M:%S %Z') \
                .replace(tzinfo=timezone('UTC'))
            date_time_eastern_object = date_time_utc_object.astimezone(timezone('US/Eastern'))
            date_time_sql = date_time_eastern_object.strftime('%Y-%m-%d %H:%M:%S')
            date_time_pt_object = date_time_utc_object.astimezone(timezone('US/Pacific'))
            date_time_pt = date_time_pt_object.strftime('%m/%d/%y %-I:%M %p %Z')
            date = date_time_pt_object.strftime('%Y-%m-%d')

            title = entry.title
            link = entry.link.split('?')[0]
            if is_english_story(link):
                output.append({'ticker': ticker_object, 'title': title, 'description': description, 'date_time': date_time_pt,
                               'link': link, 'date': date, 'date_time_sql': date_time_sql, 'source': 'Business Wire'})

    return output


def filter_bus_wire_news_feed_with_nonsequential_keywords(url, keywords):
    """
    Filter articles using non-sequential keywords
    # NOTE: THIS IS UNTESTED
    :param url: url of RSS feed
    :param keywords: list of keywords
    :return: list of article objects
    """
    news_stories = ping_bus_wire_rss_news_feed(url)
    output = []
    for entry in news_stories:
        description = entry['description']
        ticker_object = get_ticker_from_description(description)
        if ticker_object:
            for keyword in keywords:
                if keyword in description and keyword == keywords[-1]:
                    output.append(entry)
                else:
                    # If any of the keywords do not match, go to next news story
                    break

    return output


def initialize_browser():
    """
    Initialized Chrome browser for Selenium
    :return: Browser object
    """
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    browser = webdriver.Chrome(options=options)
    return browser


def is_english_story(url):
    """
    Checks url for language
    :param url: URL of article
    :return: True if it's an English artcle, False if not
    """
    if '/en/' in url:
        return True
    else:
        return False


def get_stories_from_search_page(url, browser):
    """
    Retrieve all articles that exist on a search page
    :param url: URL of search
    :param browser: Browser object
    :return: List of article objects
    """
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

        # Take text from each object and put in lists
        date_text = [elem.text for elem in date_elems]
        title_text = [elem.text for elem in title_elems]
        heading_text = [elem.text for elem in heading_elems]
        urls = [elem.get_attribute('href') for elem in url_elems]

        output = []
        for i, n in enumerate(urls):
            ticker_object = get_ticker_from_description(heading_text[i])
            if is_english_story(urls[i]) and ticker_object:
                date = normalize_date_return_object(date_text[i])
                article_object = NewsArticle(date, title_text[i], ticker_object, heading_text[i], urls[i],
                                             'BusinessWire')
                output.append(article_object)

        return output
    except TimeoutException:
        return []


def find_min_date_on_search_results_page(url, browser):
    """
    Find the minimum date of all the articles on the page (to determine when to stop paginating)
    :param url: Url of search
    :param browser: Browser object
    :return: Minimum date (if it exists), None if none exists
    """
    browser.get(url)
    timeout = 20
    try:
        # Wait until the bottom image element loads before reading in data.
        WebDriverWait(browser, timeout). \
            until(EC.visibility_of_element_located((By.XPATH, '//*[@id="bw-group-all"]/div/div/div[3]/section')))
        # Original path to wait: '//*[@id="bw-group-all"]/div/div/div[3]/section/ul/li[last()]/p')))

        # Retrieve min date from page
        min_date_text = browser.find_element_by_xpath('//*[@id="bw-group-all"]/div/div/div[3]/section/'
                                                      'ul/li[last()]/div[1]/time').text

        min_date = normalize_date_return_object(min_date_text)

        return min_date
    except (TimeoutException, NoSuchElementException):
        return None


def find_story_from_ticker_date(ticker, date_string, browser):
    """
    Pulls stories that match a search for a specific ticker and date combination
    :param ticker: Company ticker
    :param date_string: Date
    :param browser: Browser object
    :return: Dictionary of story object lists from the date searched, as well as the date before.
    """

    # Initialize variable to keep it happy
    min_date_on_page = datetime.datetime.today()

    # Turn date_string into object for comparison
    date_object_of_event = normalize_date_return_object(date_string)
    date_object_day_before_event = date_object_of_event + datetime.timedelta(-1)

    url_page = 1
    same_day_stories = []
    prev_day_stories = []

    # While the minimum date on the results page is greater than the event, keep paginating
    while min_date_on_page >= date_object_day_before_event:
        url = 'https://www.businesswire.com/portal/site/home/search/?searchType=ticker&searchTerm=' \
              + ticker + '&searchPage=' + str(url_page)

        min_date_on_page = find_min_date_on_search_results_page(url, browser)
        if min_date_on_page is None:
            break
        url_page += 1

        if min_date_on_page <= date_object_day_before_event or min_date_on_page == date_object_of_event:
            search_page_details = get_stories_from_search_page(url, browser)

            for story in search_page_details:
                if story.date == date_object_of_event:
                    print('Same day = ' + story.title)
                    same_day_stories.append(story)

                if story.date == date_object_of_event + datetime.timedelta(-1):
                    print('Prev day = ' + story.title)
                    prev_day_stories.append(story)

    return {'same_day_stories': same_day_stories, 'prev_day_stories': prev_day_stories}



