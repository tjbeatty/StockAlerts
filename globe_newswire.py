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


class GlobeNewswireArticle:
    def __init__(self, date, title, ticker, description, url):
        self.date = date
        self.title = title
        self.ticker = ticker
        self.description = description
        self.url = url

    def __getitem__(self, item):
        return item


def ping_gnw_rss_news_feed(url):
    feed = feedparser.parse(url)
    output = []
    for entry in feed.entries:
        ticker = False
        for i, tag in enumerate(entry.tags):
            if get_ticker_from_description(entry.tags[i].term):
                ticker = get_ticker_from_description(entry.tags[i].term)

        if ticker and entry.language == 'en':
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
            link = entry.link

            output.append({'ticker': ticker, 'title': title, 'description': description, 'date_time': date_time_pt,
                           'link': link, 'date': date, 'date_time_sql': date_time_sql, 'source': 'Globe Newswire'})

    return output


def filter_gnw_news_feed_with_nonsequential_keywords(url, keywords):
    news_stories = ping_gnw_rss_news_feed(url)
    output = []
    for entry in news_stories:
        description = entry['description']
        ticker = get_ticker_from_description(description)
        if ticker:
            for keyword in keywords:
                if keyword in description and keyword == keywords[-1]:
                    output.append(entry)
                else:
                    # If any of the keywords do not match, go to next news story
                    break

    return output


def initialize_browser(arguments='headless'):
    options = webdriver.ChromeOptions()
    options.add_argument(arguments)
    browser = webdriver.Chrome(options=options)
    return browser


def check_for_no_stories(browser):
    try:
        no_stories = browser.find_element_by_xpath('/html/body/div[1]/div[2]/div/p').text
        if 'No articles were found' in no_stories:
            return True
        else:
            return False
    except NoSuchElementException:
        return False


def check_for_next_page_button(browser):
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
            ticker = get_ticker_from_description(heading_text[i])
            if ticker:
                date = normalize_date_return_object(date_text[i])
                article_object = GlobeNewswireArticle(date, title_text[i], ticker, heading_text[i], urls[i])
                output.append(article_object)

        return output
    except TimeoutException:
        return []


def find_story_from_ticker_date(ticker, date_begin_string, browser, exchange='', date_end_string=''):

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
            if get_ticker_from_description(story.description) == ticker:
                all_stories.append(story)

        url_page += 1
    return all_stories


def find_story_from_ticker_two_days(ticker, date_string, browser, exchange=''):
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
