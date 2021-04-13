import feedparser
from pytz import timezone
import re
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import datetime
from stocks_info import normalize_date_return_object
from time import sleep
from stocks_info import get_ticker_from_description
from stock_alert_classes import NewsArticle


def ping_gnw_rss_news_feed(url):
    """
    Pings a Global Newswire rss feed and returns all articles present
    :param url: url of RSS feed
    :return: list of article objects
    """
    feed = feedparser.parse(url)
    output = []
    for entry in feed.entries:
        ticker_object = False
        for i, tag in enumerate(entry.tags):
            if get_ticker_from_description(entry.tags[i].term):
                ticker_object = get_ticker_from_description(entry.tags[i].term)

        if ticker_object and entry.language == 'en':
            date_time_utc = entry.published
            date_time_utc_object = datetime.datetime.strptime(date_time_utc, '%a, %d %b %Y %H:%M %Z') \
                .replace(tzinfo=timezone('UTC'))
            date_time_eastern_object = date_time_utc_object.astimezone(timezone('US/Eastern'))
            date_time_sql = date_time_eastern_object.strftime('%Y-%m-%d %H:%M:%S')
            date_time_pt_object = date_time_utc_object.astimezone(timezone('US/Pacific'))
            date_time_pt = date_time_pt_object.strftime('%m/%d/%y %-I:%M %p %Z')
            date = date_time_pt_object.strftime('%Y-%m-%d')

            description_html = entry.description
            description = re.sub('<[^<]+?>', '', description_html)
            title = entry.title
            link = entry.link.split('?')[0]

            output.append({'ticker': ticker_object, 'title': title, 'description': description, 'date_time': date_time_pt,
                           'link': link, 'date': date, 'date_time_sql': date_time_sql, 'source': 'Globe Newswire'})

    return output


def filter_gnw_news_feed_with_nonsequential_keywords(url, keywords):
    """
    Filter articles using non-sequential keywords
    # NOTE: THIS IS UNTESTED
    :param url: url of RSS feed
    :param keywords: list of keywords
    :return: list of article objects
    """
    news_stories = ping_gnw_rss_news_feed(url)
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


def initialize_browser(arguments='headless'):
    """
    Initializes a browser for Selenium
    :param arguments: arguments for browser setup
    :return: Browser object
    """
    options = webdriver.ChromeOptions()
    options.add_argument(arguments)
    browser = webdriver.Chrome(options=options)
    return browser


def check_for_no_stories(browser):
    """
    Looks at the Selenium browser page to determine if there were no stories returned for the search
    :param browser: Browser object
    :return: True, if no articles returned. False, if articles on page
    """
    try:
        no_stories = browser.find_element_by_xpath('/html/body/div[1]/div[2]/div/p').text
        if 'No articles were found' in no_stories:
            return True
        else:
            return False
    except NoSuchElementException:
        return False


def check_for_next_page_button(browser):
    """
    Looks at the Selenium browser page for a "Next page" button
    :param browser: Browser object
    :return: True, if "Next page" button. False, if no button found
    """
    try:
        # Check for next page
        next_page_text = browser.find_element_by_xpath('/html/body/div[1]/div[2]/div/div[13]/div[3]/a/span[1]').text
        if next_page_text:
            return True
        else:
            return False

    except (TimeoutException, NoSuchElementException) as e:
        return False


def get_stories_from_search_page(url, browser):
    """
    Returns all stories from the current search page
    :param url: url of search results
    :param browser: Browser parameter
    :return: List of article objects
    """
    browser.get(url)
    timeout = 20

    try:
        if check_for_no_stories(browser):
            return []

        # Wait until the bottom image element loads before reading in data.
        WebDriverWait(browser, timeout). \
            until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[2]/div/div[2]/span')))
        # Retrieve dates, title, desrciption, url from each story
        date_elems = browser.find_elements_by_xpath('/html/body/div[1]/div[2]/div/div[*]/div/div[2]/div/span[1]')
        title_elems = browser.find_elements_by_xpath('/html/body/div[1]/div[2]/div/div[*]/div/div[2]/a')
        heading_elems = browser.find_elements_by_xpath('/html/body/div[1]/div[2]/div/div[*]/div/div[2]/span')
        url_elems = browser.find_elements_by_xpath('/html/body/div[1]/div[2]/div/div[*]/div/div[2]/a')
        # Take text from each object and put in lists
        date_text = [elem.text for elem in date_elems]
        title_text = [elem.text for elem in title_elems]
        heading_text = [elem.text for elem in heading_elems]
        urls = [elem.get_attribute('href') for elem in url_elems]

        output = []
        for i, n in enumerate(urls):
            ticker_object = get_ticker_from_description(heading_text[i])
            if ticker_object:
                date = normalize_date_return_object(date_text[i])
                article_object = NewsArticle(date, title_text[i], ticker_object, heading_text[i], urls[i], 'Globe Newswire')
                output.append(article_object)

        return output
    except TimeoutException:
        return []


def find_story_from_ticker_date(ticker, date_begin_string, browser, exchange='', date_end_string=''):
    """
    Searches GlobeNewswire for by ticker and date.
    :param ticker: Company ticker
    :param date_begin_string: Begin date for search. If there is no end date, this is also the end date.
    :param browser: Browser object
    :param exchange: Exchange on which the ticker is traded
    :param date_end_string: (optional) End date of search
    :return: List of article objects
    """
    # Turn date_string into object for comparison
    date_start_object = normalize_date_return_object(date_begin_string)
    date_start_str = date_start_object.strftime('%Y-%m-%d')

    if date_end_string != '':
        date_end_object = normalize_date_return_object(date_end_string)
        date_end_str = date_end_object.strftime('%Y-%m-%d')
    else:
        date_end_str = date_start_str

    url_page = 1
    all_stories = []
    next_page_button = True
    # While the there is a "Next Page" button on the page, keep paginating
    while next_page_button:
        keyword = ticker
        if exchange:
            keyword = keyword + "," + exchange

        url = 'https://www.globenewswire.com/search/lang/en/exchange/nyse,nasdaq/date/[' + date_start_str + \
              '%2520TO%2520' + date_end_str + ']/keyword/' + keyword + \
              '?page=' + str(url_page)

        next_page_button = check_for_next_page_button(browser)
        search_page_details = get_stories_from_search_page(url, browser)

        for story in search_page_details:
            # TODO - add the ability to also ensure the exchange is the same
            tickers_in_story = get_ticker_from_description(story.description)
            tickers_only = [i.ticker for i in tickers_in_story]
            if ticker in tickers_only:
                all_stories.append(story)

        url_page += 1
    return all_stories


def find_story_from_ticker_two_days(ticker, date_string, browser, exchange=''):
    """
    Finds all stories from a ticker, the date specified, and the date before.
    :param ticker: Company ticker
    :param date_string: Date of event
    :param browser: Browser object
    :param exchange: Exchange of ticker
    :return: Dictionary of a list of stories on the day of event, and a list of stories the day before the event.
    """
    date_start_object = normalize_date_return_object(date_string)
    date_str = date_start_object.strftime('%Y-%m-%d')
    day_before_obj = date_start_object + datetime.timedelta(-1)
    day_before_str = day_before_obj.strftime('%Y-%m-%d')
    same_day_stories = []
    prev_day_stories = []

    stories = find_story_from_ticker_date(ticker, day_before_str, browser, exchange, date_str)
    sleep(1)
    for story in stories:
        if story.date.date() == date_start_object.date():
            print('Same day = ' + story.title)
            same_day_stories.append(story)

        if story.date.date() == day_before_obj.date():
            print('Prev day = ' + story.title)
            prev_day_stories.append(story)

    return {'same_day_stories': same_day_stories, 'prev_day_stories': prev_day_stories}
