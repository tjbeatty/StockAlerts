from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import csv


def pull_article_gnw(url):
    """
    Pull the article text from a GlobeNewsire url
    :param url: GlobeNewswire URL
    :return: Article text
    """
    page = urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')

    main_body = soup.find_all('div', id='main-body-container')

    # Full article, including "About" and "Forward-looking" statements
    full_article = main_body[0].text.strip()
    # There's a chance it will remove some of this
    only_article = full_article.split('\nAbout ')[0]

    return only_article


def pull_article_bw(url):
    """
    Pull the article text from a Business Wire url
    :param url: Business Wire URL
    :return: Article text
    """
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    page = urlopen(req).read()
    soup = BeautifulSoup(page, 'html.parser')
    main_body = soup.find('div', itemprop='articleBody').find_all('p')
    full_article = ''
    for p in main_body:
        p = p.text.strip()
        full_article = full_article + ' ' + p

    return full_article


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

# filename = 'extreme_events_same_day_gnw_bw_stories.csv'
#
# # Read in file
# df = pd.read_csv(filename)
# # Launch vader sentiment analysis
# vader = SentimentIntensityAnalyzer()
# # Lambda function to pull sentiment from text
# pos_minus_neg_sentiment = lambda text: vader.polarity_scores(text)['pos'] - vader.polarity_scores(text)['neg']
# compound_sentiment = lambda text: vader.polarity_scores(text)['compound']
# article_text = lambda url: pull_article(url)
#
# # Apply sentiment analysis to title and description fields
# df['title_compound'] = df['title'].apply(compound_sentiment)
# df['description_compound'] = df['description'].apply(compound_sentiment)
# df['article_compound'] = df['url'].apply(article_text).apply(compound_sentiment)
# df['title_pmn'] = df['title'].apply(pos_minus_neg_sentiment)
# df['description_pmn'] = df['description'].apply(pos_minus_neg_sentiment)
# df['article_pmn'] = df['url'].apply(article_text).apply(pos_minus_neg_sentiment)

# df.to_csv('sentiment_analysis_out2.csv', index=False)