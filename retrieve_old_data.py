from scrape_old_business_wire import old_bus_wire_news_from_search_term
from scrape_old_gnw import old_gnw_news_from_search_term
from business_wire import find_story_from_ticker_date, initialize_browser
from globe_newswire import check_for_no_stories
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from stocks_info import get_ticker_objects_from_description, normalize_date_return_object
from stock_alert_classes import NewsArticle
import traceback


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


def get_stories_from_search_page(url, source, browser):
    """
    Returns all stories from the current search page
    :param url: url of search results
    :param browser: Browser parameter
    :return: List of article objects
    """
    browser.get(url)
    timeout = 20
    print('in get stories')
    try:
        # If the source is Globe Newswire, use one xpath to find elements
        if source == 'gnw':
            print('in gnw')
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
            source_long = 'Globe Newswire'
        # If the source is Business Wire, use another xpath to find elements
        elif source == 'bw':
            # Wait until the bottom image element loads before reading in data.
            WebDriverWait(browser, timeout). \
                until(EC.visibility_of_element_located((By.XPATH, '//*[@id="bw-group-all"]/div/div/div[3]/'
                                                                  'section/ul/li[last()]/p')))
            # Retrieve dates, title, desciption, url from each story
            date_elems = browser.find_elements_by_xpath(
                '//*[@id="bw-group-all"]/div/div/div[3]/section/ul/li[*]/div[1]/time')
            title_elems = browser.find_elements_by_xpath(
                '//*[@id="bw-group-all"]/div/div/div[3]/section/ul/li[*]/h3/a')
            heading_elems = browser.find_elements_by_xpath(
                '//*[@id="bw-group-all"]/div/div/div[3]/section/ul/li[*]/p')
            url_elems = browser.find_elements_by_xpath(
                '//*[@id="bw-group-all"]/div/div/div[3]/section/ul/li[*]/h3/a')
            source_long = 'Business Wire'

        # Take text from each object and put in lists
        date_text = [elem.text for elem in date_elems]
        title_text = [elem.text for elem in title_elems]
        heading_text = [elem.text for elem in heading_elems]
        urls = [elem.get_attribute('href') for elem in url_elems]

        output = []
        for i, n in enumerate(urls):
            if is_english_story(n):
                ticker_object_list = get_ticker_objects_from_description(heading_text[i])
                if ticker_object_list:
                    date = normalize_date_return_object(date_text[i])
                    article_object = NewsArticle(date, title_text[i], ticker_object_list,
                                                 heading_text[i], n, source_long)
                    output.append(article_object)
        return output

    except TimeoutException as e:
        print(e)
        return None


def old_news_from_search_term(search_term, num_articles, browser, source, page_start=1):
    """
    Pull all BusinessWire news related to a search term, up to a certain number of articles
    :param search_term: Search term
    :param num_articles: Number of article to retrieve
    :param browser: The initialized Selinium browser
    :param page_start: The search page to start on (in case
    :return: Outputs a CSV of all the articles
    """
    if 'bw' in source.lower() or 'business wire' in source.lower():
        source = 'bw'
    elif 'gnw' in source.lower() or 'globe newswire' in source.lower():
        source = 'gnw'

    articles_retrieved = 0
    page = page_start
    output = []
    try:
        while articles_retrieved < num_articles:
            print(page)
            print("Found " + str(articles_retrieved) + " articles...")

            if source == 'bw':
                url = 'https://www.businesswire.com/portal/site/home/search/?searchType=news&searchTerm=' \
                      + search_term + '&searchPage=' + str(page)
            elif source == 'gnw':
                url = 'https://www.globenewswire.com/search/lang/en/exchange/nyse,nasdaq/keyword/' \
                     + search_term + '?page=' + str(page)

            articles_found = get_stories_from_search_page(url, source, browser)
            page = page + 1

            for story in articles_found:
                articles_retrieved = articles_retrieved + 1
                output.append(story)

        return output
    except:
        traceback.print_exc()


# def retrieve_old_articles_and_data_for_keyword(search_term, num_articles, source):
#     browser = initialize_browser()
#     if 'bw' in source.lower() or 'business wire' in source.lower():
#         articles_returned = old_bus_wire_news_from_search_term(search_term, num_articles, browser)
#     elif 'gnw' in source.lower() or 'globe newswire' in source.lower():
#         articles_returned = old_gnw_news_from_search_term(search_term)
#
#
#     with open(filename_in, 'r') as csv_in:
#         csv_reader = csv.reader(csv_in)
#         header_throwaway = next(csv_reader)
#
#         for row in csv_reader:
#             [date, ticker, pct_change_prev_close, day_percent_change, max_day_percent_change, source, title,
#              description, url, same_or_prev] = row
#
#             article = pull_article(url)
#             article_date_time = article['article_object'].date_time
#             article_text = article['article_text']
#             article_dt_str = article_date_time.strftime('%m/%d/%Y %H:%M')
#             article_date = article_date_time.date()
#             # If the article was after 4:30, it will apply to the next day's stock change
#             article_stock_affect_date = apply_article_same_or_next_day(article_date_time)
#             row.append(article_dt_str)
#
#             if (article_date == article_stock_affect_date and same_or_prev == 'same') or \
#                 (article_date != article_stock_affect_date and same_or_prev == 'prev'):
#                 sentiments = get_sentiments(title, description, article_text)
#                 try:
#                     #  Sentiment analysis
#                     nltk_pos_minus_neg_title = sentiments["nltk_pos_minus_neg_title"]
#                     nltk_pos_minus_neg_description = sentiments["nltk_pos_minus_neg_description"]
#                     nltk_pos_minus_neg_article = sentiments["nltk_pos_minus_neg_article"]
#                     nltk_compound_title = sentiments["nltk_compound_title"]
#                     nltk_compound_description = sentiments["nltk_compound_description"]
#                     nltk_compound_article = sentiments["nltk_compound_article"]
#                     tb_polarity_title = sentiments["tb_polarity_title"]
#                     tb_polarity_description = sentiments["tb_polarity_description"]
#                     tb_polarity_article = sentiments["tb_polarity_article"]
#                     stanza_sentiment_article = sentiments["stanza_sentiment_article"]
#
#                     sentiments_list = [nltk_pos_minus_neg_title, nltk_pos_minus_neg_description, nltk_pos_minus_neg_article,
#                                        nltk_compound_title, nltk_compound_description, nltk_compound_article,
#                                        tb_polarity_title, tb_polarity_description, tb_polarity_article,
#                                        stanza_sentiment_article]
#
#                     row.extend(sentiments_list)
#                     stock_date_info = get_data_ticker_date_iex(ticker, date)
#
#                     open_price = stock_date_info['open_price']
#                     close_price = stock_date_info['close_price']
#                     percent_change = stock_date_info['percent_change']
#                     max_percent_change = stock_date_info['max_percent_change']
#                     volume = stock_date_info['volume']
#                     average_volume = get_average_volume(ticker)
#
#                     stock_data_list = [open_price, close_price, percent_change, max_percent_change, volume, average_volume]
#                     row.extend(stock_data_list)
#                     with open(filename_out, 'a+') as csv_out:
#                         csv_writer = csv.writer(csv_out)
#                         csv_writer.writerow(row)
#                 except (IndexError, JSONDecodeError, TypeError):
#                     None

print(old_news_from_search_term('fda', 25, initialize_browser('incognito'), 'gnw'))