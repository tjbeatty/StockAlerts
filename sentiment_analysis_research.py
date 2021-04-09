from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import csv


def pull_article_gnw(url):
    page = urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')

    main_body = soup.find_all('div', id='main-body-container')

    # Full article, including "About" and "Forward-looking" statements
    full_article = main_body[0].text.strip()
    # There's a chance it will remove some of this
    only_article = full_article.split('\nAbout ')[0]

    return only_article


def pull_article_bw(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    page = urlopen(req).read()
    soup = BeautifulSoup(page, 'html.parser')
    main_body = soup.find('div', itemprop='articleBody').find_all('p')
    full_article = ''
    for p in main_body:
        p = p.text.strip()
        full_article = full_article + ' ' + p

    return full_article


# filename = 'extreme_events_same_day_gnw_bw_stories.csv'
# with open(filename, 'r') as csv_in:
#
#     csv_reader = csv.reader(csv_in)
#     header = next(csv_reader)
#
# for row in csv_reader:
#     [date, ticker, pct_change_prev_close, day_percent_change, max_day_percent_change, source, title,
#      description, url, same_or_prev] = row
#
#
#
#
# # Read in file
# df = pd.read_csv(filename)
# # Launch vader sentiment analysis
# vader = SentimentIntensityAnalyzer()
# # Lambda function to pull sentiment from text
# f = lambda text: vader.polarity_scores(text)['compound']
#
# # Apply sentiment analysis to title and description fields
# df['title_sentiment'] = df['title'].apply(f)
# df['description_sentiment'] = df['description'].apply(f)

