from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from general_functions import get_ticker_objects_from_description, normalize_date_return_object, \
    is_english_story, initialize_browser
from stock_alert_classes import NewsArticle
import traceback
from stocks_info import get_data_ticker_date_iex, get_average_volume, date_article_reflected_in_stock, \
    get_company_info_iex, get_shares_outstanding
import csv
from json.decoder import JSONDecodeError
import os.path
import re
from globe_newswire import pull_article_gnw
from business_wire import pull_article_bw


def pull_article(url):
    """
    Pulls article text from a GNW or BW text
    :param url:
    :return: Article text, if present. False if no text present
    """
    if 'globenewswire' in url.lower():
        return pull_article_gnw(url)
    elif 'businesswire' in url.lower():
        return pull_article_bw(url)
    else:
        return False


def check_for_no_stories(source, browser):
    """
    Looks at the Selenium browser page to determine if there were no stories returned for the search
    :param browser: Browser object
    :return: True, if no articles returned. False, if articles on page
    """
    if source == 'gnw':
        try:
            no_stories = browser.find_element_by_xpath('/html/body/div[1]/div[2]/div/p').text
            if 'No articles were found' in no_stories:
                return True
            else:
                return False
        except NoSuchElementException:
            return False
    elif source == 'bw':
        try:
            no_stories = browser.find_element_by_xpath('/html/body/div[1]/div/div/div/div/div[3]/section/h2').text
            if 'no results found' in no_stories:
                return True
            else:
                return False
        except NoSuchElementException:
            return False


def get_stories_from_search_page(url, source, browser):
    """
    Returns all stories from the current search page
    :param url: url of search results
    :param browser: Browser parameter
    :return: List of article objects
    """
    browser.get(url)
    timeout = 20
    try:
        # If the source is Globe Newswire, use one xpath to find elements
        if check_for_no_stories(source, browser):
            return None

        if source == 'gnw':
            # Wait until the bottom image element loads before reading in data.
            WebDriverWait(browser, timeout). \
                until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[2]/div[*]/div[1]/div[2]/span')))
            # Retrieve dates, title, desrciption, url from each story
            date_elems = browser.find_elements_by_xpath('/html/body/div[1]/div[2]/div/div[2]/div[*]/div/div[2]/div/span[1]')
            '/html/body/div[1]/div[2]/div/div[2]/div[*]/div/div[2]/div/span[1]'
            title_elems = browser.find_elements_by_xpath('/html/body/div[1]/div[2]/div/div[2]/div[*]/div/div[2]/a')
            heading_elems = browser.find_elements_by_xpath('/html/body/div[1]/div[2]/div/div[2]/div[*]/div/div[2]/span')
            url_elems = browser.find_elements_by_xpath('/html/body/div[1]/div[2]/div/div[2]/div[*]/div/div[2]/a')
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
        title_text = [elem.text.strip() for elem in title_elems]
        heading_text = [elem.text.strip() for elem in heading_elems]
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

    except (TimeoutException) as e:
        print('TimeoutException')
        return None


def get_articles_from_keyword(search_term, num_articles, source, browser, start_page=1):
    """
    Pull all BusinessWire news related to a search term, up to a certain number of articles
    :param search_term: Search term
    :param num_articles: Number of article to retrieve
    :param source: Which news source to pull articles from
    :param browser: The initialized Selinium browser
    :param start_page: The search page to start on (in case
    :return: Outputs a CSV of all the articles
    """
    if 'bw' in source.lower() or 'business wire' in source.lower():
        source = 'bw'
    elif 'gnw' in source.lower() or 'globe newswire' in source.lower():
        source = 'gnw'

    articles_retrieved = 0
    page = start_page
    output = []
    try:
        while articles_retrieved < num_articles:
            print("Found " + str(articles_retrieved) + " articles...")

            if source == 'bw':
                url = 'https://www.businesswire.com/portal/site/home/search/?searchType=news&searchTerm=' \
                      + search_term + '&searchPage=' + str(page)
            elif source == 'gnw':
                url = 'https://www.globenewswire.com/search/lang/en/exchange/nyse,nasdaq/keyword/' \
                     + search_term + '?page=' + str(page)

            articles_found = get_stories_from_search_page(url, source, browser)

            for story in articles_found:
                articles_retrieved = articles_retrieved + 1
                output.append(story)

            print("Finished results page " + str(page) + ' on ' + source)
            page = page + 1
        return output
    except:
        traceback.print_exc()


def get_articles_and_data_from_keyword(search_term, num_articles, source, start_page=1, filename=None):
    browser = initialize_browser()
    # article_list = get_articles_from_keyword(search_term, num_articles, source, browser, start_page)
    if filename is None:
        filename_out = 'csvs/' + search_term + '_' + source + '_' + str(num_articles) + '.csv'
    else:
        filename_out = filename
    header = ['date', 'ticker', 'source', 'title', 'description', 'url', 'date_time_story', 'open_price',
              'close_price', 'percent_change', 'max_percent_change', 'min_percent_change', 'volume', 'average_volume',
              'tags', 'primary_sic_code', 'employees', 'shares_outstanding', 'marketcap_open']
    # Check if document exists
    if not os.path.isfile(filename_out):
        with open(filename_out, 'w') as csv_out:
            csv_writer = csv.writer(csv_out)
            csv_writer.writerow(header)

    if 'bw' in source.lower() or 'business wire' in source.lower():
        source = 'bw'
    elif 'gnw' in source.lower() or 'globe newswire' in source.lower():
        source = 'gnw'

    articles_retrieved = 0
    page = start_page
    output = []
    try:
        while articles_retrieved < num_articles:
            if source == 'bw':
                url = 'https://www.businesswire.com/portal/site/home/search/?searchType=news&searchTerm=' \
                      + search_term + '&searchPage=' + str(page)
            elif source == 'gnw':
                url = 'https://www.globenewswire.com/search/lang/en/exchange/nyse,nasdaq/keyword/' \
                      + search_term + '?page=' + str(page)

            articles_found = get_stories_from_search_page(url, source, browser)
            if articles_found is None:
                break

            for news_story in articles_found:
                try:
                    url = news_story.url
                    article_obj_and_text = pull_article(url)
                    article_date_time = article_obj_and_text['article_object'].date_time
                    article_ticker_objects = article_obj_and_text['article_object'].ticker_object_list
                    article_title = re.sub('\n', '', article_obj_and_text['article_object'].title.strip())
                    article_description = re.sub('\n', '', article_obj_and_text['article_object'].description.strip())
                    article_description = re.sub('NBSP', ' ', article_description)
                    article_text = article_obj_and_text['article_text']
                    article_dt_str = article_date_time.strftime('%m/%d/%Y %H:%M')

                    # If the article was after 4:00 or a weekend/holiday, it will apply to the next trading day's stock change
                    article_stock_effect_date = date_article_reflected_in_stock(article_date_time)

                    tickers_list = [ticker_object.ticker for ticker_object in article_ticker_objects]
                    for ticker in tickers_list:
                        stock_date_info = get_data_ticker_date_iex(ticker, article_stock_effect_date)

                        open_price = stock_date_info['open_price']
                        close_price = stock_date_info['close_price']
                        percent_change = stock_date_info['percent_change']
                        max_percent_change = stock_date_info['max_percent_change']
                        min_percent_change = stock_date_info['min_percent_change']
                        volume = stock_date_info['volume']
                        average_volume = get_average_volume(ticker)

                        company_info = get_company_info_iex(ticker)
                        tags = company_info['tags']
                        sic_code = company_info['primary_sic_code']
                        employees = company_info['employees']

                        shares_outstanding = get_shares_outstanding(ticker)
                        market_cap_open = shares_outstanding * open_price

                        stock_data_list = [open_price, close_price, percent_change, max_percent_change,
                                           min_percent_change, volume, average_volume, tags, sic_code, employees,
                                           shares_outstanding, market_cap_open]

                        row = [article_stock_effect_date, ticker, source, article_title, article_description, url,
                               article_dt_str]
                        row.extend(stock_data_list)

                        with open(filename_out, 'a+') as csv_out:
                            csv_writer = csv.writer(csv_out)
                            csv_writer.writerow(row)
                            articles_retrieved = articles_retrieved + 1
                            print("Wrote " + str(articles_retrieved) + " articles to file...")

                except (IndexError, JSONDecodeError, TypeError):
                    None
            print("Finished results page " + str(page))
            page = page + 1
        browser.quit()

    except:
        page = page + 1
        traceback.print_exc()
        return page


# fda_words = ['phase 1', 'phase 2', 'phase 3', 'phase i', 'phase ii', 'phase iii', 'phase 0',
#              'pharmaceuticals', 'therapeutics', 'medical']  # , 'fda']
# executive_words = ['ceo', 'cto', 'cfo', 'coo', 'chief', 'officer', 'board', 'president', 'director']
# announce_words = ['appoint', 'name', 'announce', 'promote', 'join']
#
# search_terms = fda_words
# for i in executive_words:
#     for j in announce_words:
#         executive_appointment_phrase = i + ' ' + j
#         search_terms.append(executive_appointment_phrase)
# print(search_terms)

# for source in ['bw', 'gnw']:
#     get_articles_and_data_from_keyword('fda', 300, source)
#
# for term in search_terms:
#     for source in ['bw', 'gnw']:
#         print('Searching for ' + term + ' from ' + source)
#         get_articles_and_data_from_keyword(term, 50, source)

def loop_until_article_goal_achieved(search_term, articles_to_get, source, start_page=1, filename=None):
    if filename is None:
        filename_out = 'csvs/' + search_term + '_' + source + '_' + str(articles_to_get) + '.csv'
    else:
        filename_out = 'csvs/' + filename

    if not os.path.isfile(filename_out):
        articles_already_gotten = 0
        articles_left = articles_to_get
    else:
        with open(filename_out, 'r') as csv_in:
            articles_already_gotten = len(csv_in.readlines())
            articles_left = articles_to_get - articles_already_gotten
            print('Articles left to get: ' + str(articles_left))

    while articles_already_gotten < articles_to_get:
        start_page = get_articles_and_data_from_keyword(search_term, articles_left, source, start_page, filename_out)


# loop_until_article_goal_achieved('fda', 10000, 'gnw', 895)
loop_until_article_goal_achieved('fda', 10000, 'bw', 2804)
