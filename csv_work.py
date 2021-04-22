import csv
from bs4 import BeautifulSoup
import urllib.request
import requests
import datetime
from globe_newswire import pull_article_date_time_gnw
from business_wire import pull_article_date_time_bw
from sentiment_analysis_research import pull_article, get_sentiments


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

# events_to_keep = []
# fda_stories = []
# investigations = []
# financial_stories = []
# executive_announcements = []
# other_stories = []
# fda_words = ['fda', 'phase 1', 'phase 2', 'phase 3', 'phase i', 'phase ii', 'phase iii', 'phase 0', 'pharmaceuticals',
#              'therapeutics']
# financial_words = ['sales results', 'financials', 'provides update', 'business update', 'financial results',
#                    'first quarter', 'second quarter', 'third quarter', 'fourth quarter', 'full year', 'year end',
#                    'first-quarter', 'second-quarter', 'third-quarter', 'fourth-quarter', 'full-year', 'year-end',
#                    'annual report', 'corporate update', 'year-to-date', 'fiscal year']
# executive_words = ['ceo', 'cto', 'cfo', 'coo', 'chief', 'officer', 'board', 'president', 'director']
# announce_words = ['appoint', 'name', 'announce', 'promote', 'name', 'join']
# investigation_words = ['investigation', 'investor', 'alert', 'shareholder notice', 'shareholder alert', 'law office']


filename_in = 'executive_announcements.csv'
file_out = 'executive_announcements_filtered.csv'
output = []


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

            output.append(row)
        # for keyword in investigation_words:
        #     if keyword in title.lower() and saved == 0:
        #         investigations.append(row)
        #         saved = 1
        #         break
        # for keyword in financial_words:
        #     if (keyword in description.lower() or keyword in title.lower()) and saved == 0:
        #         financial_stories.append(row)
        #         saved = 1
        #         break
        # for keyword in fda_words:
        #     if keyword in description.lower() and saved == 0:
        #         fda_stories.append(row)
        #         saved = 1
        #         break
        # for keyword in executive_words:
        #     if keyword in title.lower() and saved == 0:
        #         for announce_word in announce_words:
        #             if announce_word in title.lower():
        #                 executive_announcements.append(row)
        #                 saved = 1
        #                 break
        # if saved == 0:
        #     other_stories.append(row)

    header = ['date', 'ticker', 'pct_change_prev_close', 'day_percent_change', 'max_day_percent_change', 'source',
              'title', 'description', 'url', 'same_or_prev', 'date_time_story', 'nltk_pos_minus_neg_title',
              'nltk_pos_minus_neg_description', 'nltk_pos_minus_neg_article', 'nltk_compound_title',
              'nltk_compound_description', 'nltk_compound_article', 'tb_polarity_title', 'tb_polarity_description',
              'tb_polarity_article', 'stanza_sentiment_article']

    with open(file_out, 'w') as csv_out:
        csv_writer = csv.writer(csv_out)
        csv_writer.writerow(header)

        for row in output:
            csv_writer.writerow(row)



