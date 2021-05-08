import feedparser
from pytz import timezone
import re
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import datetime
from general_functions import normalize_date_return_object, get_ticker_objects_from_description, \
    get_exchange_tickers_description, is_english_story
from stock_alert_classes import NewsArticle
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def check_for_no_stories(browser):
    """
    Looks at the Selenium browser page to determine if there were no stories returned for the search
    :param browser: Browser object
    :return: True, if no articles returned. False, if articles on page
    """
    try:
        no_stories = browser.find_element_by_xpath('//*[@id="bw-group-all"]/div/div/div[3]/section/h2').text
        print(no_stories)
        if 'no results found' in no_stories:
            return True
        else:
            return False
    except NoSuchElementException:
        return False


def pull_article_date_time_bw(url):
    """
    Returns the datetime object a Business Wire article was published
    :param url: Business Wire article url
    :return: datetime object (ET)
    """
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    page = urlopen(req).read()
    soup = BeautifulSoup(page, 'html.parser')
    date_time_str = soup.find('time')['datetime']
    date_time_utc_object = datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%SZ'). \
        replace(tzinfo=timezone('UTC'))
    date_time_eastern_object = date_time_utc_object.astimezone(timezone('US/Eastern'))

    return date_time_eastern_object


def pull_article_bw(url):
    """
    Pull the article text from a Business Wire url
    :param url: Business Wire URL
    :return: Article text
    """
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req).read()
        soup = BeautifulSoup(page, 'html.parser')
        title = soup.find('h1').text
        date_time_str = soup.find('time')['datetime']
        date_time_utc_object = datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%SZ').\
            replace(tzinfo=timezone('UTC'))
        date_time_eastern_object = date_time_utc_object.astimezone(timezone('US/Eastern'))
        all_page_text = soup.find('div', itemprop='articleBody')

        p_elems_all = all_page_text.findAll('p')
        split_index = len(p_elems_all)

        for i, p in enumerate(p_elems_all):
            # Find <p> element that starts with "About" to split
            if re.match('^[ |\n]*about', p.text.lower()):
                split_index = i
                break

        p_elems_article = p_elems_all[:split_index]
        description = p_elems_article[0].text
        article_text = ' '.join([p.text for p in p_elems_article])
        tickers = get_ticker_objects_from_description(article_text)
        return {'article_object': NewsArticle(date_time_eastern_object, title, tickers, description, url, 'Business Wire'),
                'article_text': article_text}
    except (AttributeError, HTTPError, TimeoutError):
        return None


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
        ticker_object_list = get_ticker_objects_from_description(description)

        if ticker_object_list:
            date_time_utc = entry.published + 'C'
            date_time_utc_object = datetime.datetime.strptime(date_time_utc, '%a, %d %b %Y %H:%M:%S %Z') \
                .replace(tzinfo=timezone('UTC'))
            date_time_eastern_object = date_time_utc_object.astimezone(timezone('US/Eastern'))
            date_time_pt_object = date_time_utc_object.astimezone(timezone('US/Pacific'))

            title = entry.title
            link = entry.link.split('?')[0]

            if is_english_story(link):
                news_article = NewsArticle(date_time_eastern_object, title, ticker_object_list,
                                           description, link, 'Business Wire')
                output.append(news_article)

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
        ticker_object = get_ticker_objects_from_description(description)
        if ticker_object:
            for keyword in keywords:
                if keyword in description and keyword == keywords[-1]:
                    output.append(entry)
                else:
                    # If any of the keywords do not match, go to next news story
                    break

    return output


def initialize_browser(arguments='headless'):
    """
    Initialized Chrome browser for Selenium
    :return: Browser object
    """
    options = webdriver.ChromeOptions()
    options.add_argument(arguments)
    browser = webdriver.Chrome(options=options)
    return browser


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
        if check_for_no_stories(browser):
            print(check_for_no_stories())
            return None
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
            ticker_object_list = get_ticker_objects_from_description(heading_text[i])
            if is_english_story(urls[i]) and ticker_object_list:
                date = normalize_date_return_object(date_text[i])
                article_object = NewsArticle(date[i], title_text[i], ticker_object_list[i],
                                             heading_text[i], urls[i], 'BusinessWire')
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
                if story.date_time == date_object_of_event:
                    print('Same day = ' + story.title)
                    same_day_stories.append(story)

                if story.date_time == date_object_of_event + datetime.timedelta(-1):
                    print('Prev day = ' + story.title)
                    prev_day_stories.append(story)

    return {'same_day_stories': same_day_stories, 'prev_day_stories': prev_day_stories}



