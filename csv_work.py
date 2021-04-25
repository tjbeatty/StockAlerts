import csv
from bs4 import BeautifulSoup
import urllib.request
import requests
import datetime
from globe_newswire import pull_article_date_time_gnw
from business_wire import pull_article_date_time_bw
from sentiment_analysis_research import pull_article, get_sentiments
from stocks_info import get_ticker_objects_from_description, get_average_volume
from json.decoder import JSONDecodeError


# TODO - pull company data for date
def apply_article_same_or_next_day(date_object):
    bell_close = datetime.datetime.strptime('16:30', '%H:%M').time()
    time = date_object.time()
    article_date = date_object.date()

    if time > bell_close:
        stock_date = article_date + datetime.timedelta(1)
    else:
        stock_date = article_date

    return stock_date


# output = []


def organize_articles(filename_in):
    fda_stories = []
    investigations = []
    financial_stories = []
    executive_announcements = []
    other_stories = []
    fda_words = ['fda', 'phase 1', 'phase 2', 'phase 3', 'phase i', 'phase ii', 'phase iii', 'phase 0',
                 'pharmaceuticals',
                 'therapeutics', 'medical']
    financial_words = ['sales results', 'financials', 'provides update', 'business update', 'financial results',
                       'first quarter', 'second quarter', 'third quarter', 'fourth quarter', 'full year', 'year end',
                       'first-quarter', 'second-quarter', 'third-quarter', 'fourth-quarter', 'full-year', 'year-end',
                       'annual report', 'corporate update', 'year-to-date', 'fiscal year']
    executive_words = ['ceo', 'cto', 'cfo', 'coo', 'chief', 'officer', 'board', 'president', 'director']
    announce_words = ['appoint', 'name', 'announce', 'promote', 'name', 'join']
    investigation_words = ['investigation', 'investor', 'alert', 'shareholder notice', 'shareholder alert',
                           'law office']

    with open(filename_in, 'r') as csv_in:
        csv_reader = csv.reader(csv_in)
        header_throwaway = next(csv_reader)

        for row in csv_reader:
            saved = 0
            [date, ticker, pct_change_prev_close, day_percent_change, max_day_percent_change, source, title,
             description, url, same_or_prev] = row
            ticker = ticker.replace(' ', '')
            row = [date, ticker, pct_change_prev_close, day_percent_change, max_day_percent_change, source, title,
                   description, url, same_or_prev]

            for keyword in investigation_words:
                if keyword in title.lower() and saved == 0:
                    investigations.append(row)
                    saved = 1
                    break
            for keyword in financial_words:
                if (keyword in description.lower() or keyword in title.lower()) and saved == 0:
                    financial_stories.append(row)
                    saved = 1
                    break
            for keyword in fda_words:
                if keyword in description.lower() and saved == 0:
                    fda_stories.append(row)
                    saved = 1
                    break
            for keyword in executive_words:
                if keyword in title.lower() and saved == 0:
                    for announce_word in announce_words:
                        if announce_word in title.lower():
                            executive_announcements.append(row)
                            saved = 1
                            break
            if saved == 0:
                other_stories.append(row)

        header = ['date', 'ticker', 'pct_change_prev_close', 'day_percent_change', 'max_day_percent_change', 'source',
                  'title', 'description', 'url', 'same_or_prev']

        story_lists = [fda_stories, investigations, financial_stories, executive_announcements, other_stories]
        story_types = ['fda_stories', 'investigations', 'financial_stories', 'executive_announcements', 'other_stories']

        for i, story_type in enumerate(story_types):
            with open(story_type + '.csv', 'w') as csv_out:
                csv_writer = csv.writer(csv_out)
                csv_writer.writerow(header)

                for row in story_lists[i]:
                    csv_writer.writerow(row)


def retrieve_all_data_for_csv(filename_in, filename_out):
    header = ['date', 'ticker', 'pct_change_prev_close', 'day_percent_change', 'max_day_percent_change', 'source',
              'title', 'description', 'url', 'same_or_prev', 'date_time_story', 'nltk_pos_minus_neg_title',
              'nltk_pos_minus_neg_description', 'nltk_pos_minus_neg_article', 'nltk_compound_title',
              'nltk_compound_description', 'nltk_compound_article', 'tb_polarity_title', 'tb_polarity_description',
              'tb_polarity_article', 'stanza_sentiment_article', 'open_price', 'close_price', 'percent_change',
              'max_percent_change', 'volume', 'average_volume']

    # with open(filename_out, 'w') as csv_out:
    #     csv_writer = csv.writer(csv_out)
    #     csv_writer.writerow(header)

    with open(filename_in, 'r') as csv_in:
        csv_reader = csv.reader(csv_in)
        header_throwaway = next(csv_reader)

        for row in csv_reader:
            [date, ticker, pct_change_prev_close, day_percent_change, max_day_percent_change, source, title,
             description, url, same_or_prev] = row

            article = pull_article(url)
            article_date_time = article['article_object'].date_time
            article_text = article['article_text']
            article_dt_str = article_date_time.strftime('%m/%d/%Y %H:%M')
            article_date = article_date_time.date()
            # If the article was after 4:30, it will apply to the next day's stock change
            article_stock_affect_date = apply_article_same_or_next_day(article_date_time)
            row.append(article_dt_str)

            if (article_date == article_stock_affect_date and same_or_prev == 'same') or \
                (article_date != article_stock_affect_date and same_or_prev == 'prev'):
                sentiments = get_sentiments(title, description, article_text)
                try:
                    #  Sentiment analysis
                    nltk_pos_minus_neg_title = sentiments["nltk_pos_minus_neg_title"]
                    nltk_pos_minus_neg_description = sentiments["nltk_pos_minus_neg_description"]
                    nltk_pos_minus_neg_article = sentiments["nltk_pos_minus_neg_article"]
                    nltk_compound_title = sentiments["nltk_compound_title"]
                    nltk_compound_description = sentiments["nltk_compound_description"]
                    nltk_compound_article = sentiments["nltk_compound_article"]
                    tb_polarity_title = sentiments["tb_polarity_title"]
                    tb_polarity_description = sentiments["tb_polarity_description"]
                    tb_polarity_article = sentiments["tb_polarity_article"]
                    stanza_sentiment_article = sentiments["stanza_sentiment_article"]

                    sentiments_list = [nltk_pos_minus_neg_title, nltk_pos_minus_neg_description, nltk_pos_minus_neg_article,
                                       nltk_compound_title, nltk_compound_description, nltk_compound_article,
                                       tb_polarity_title, tb_polarity_description, tb_polarity_article,
                                       stanza_sentiment_article]

                    row.extend(sentiments_list)
                    stock_date_info = get_ticker_objects_from_description(ticker, date)

                    open_price = stock_date_info['open_price']
                    close_price = stock_date_info['close_price']
                    percent_change = stock_date_info['percent_change']
                    max_percent_change = stock_date_info['max_percent_change']
                    volume = stock_date_info['volume']
                    average_volume = get_average_volume(ticker)

                    stock_data_list = [open_price, close_price, percent_change, max_percent_change, volume, average_volume]
                    row.extend(stock_data_list)
                    with open(filename_out, 'a+') as csv_out:
                        csv_writer = csv.writer(csv_out)
                        csv_writer.writerow(row)
                except (IndexError, JSONDecodeError, TypeError):
                    None


# file_list = ['financial_stories', 'investigations', 'executive_announcements', 'other_stories']
#
# for name in file_list:
#     retrieve_all_data_for_csv(name + '.csv', name + '_filtered_date.csv')

retrieve_all_data_for_csv('csvs/other_stories_edit.csv', 'csvs/other_stories_filtered_date.csv')