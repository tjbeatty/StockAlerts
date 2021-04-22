from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import csv
from textblob import TextBlob
import stanza
import re
import os
from globe_newswire import pull_article_gnw
from business_wire import pull_article_bw

os.environ['KMP_DUPLICATE_LIB_OK']='True'


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


def vader_pos_minus_neg_sentiment(text, vader=SentimentIntensityAnalyzer()):
    return vader.polarity_scores(text)['pos'] - vader.polarity_scores(text)['neg']


def vader_compound_sentiment(text, vader=SentimentIntensityAnalyzer()):
    return vader.polarity_scores(text)['compound']


def stanza_sentiment(text):
    nlp = stanza.Pipeline(lang='en', processors='tokenize,sentiment')
    doc = nlp(text)
    sentences = 0
    sentiment = 0
    for i, sentence in enumerate(doc.sentences):
        sentences += 1
        sentiment += sentence.sentiment - 1

    return sentiment / sentences


def get_sentiments(title, description, article_text):
    # TODO - Add Stanza sentiment analysis

    nltk_pos_minus_neg_title = vader_pos_minus_neg_sentiment(title)
    nltk_pos_minus_neg_description = vader_pos_minus_neg_sentiment(description)
    nltk_pos_minus_neg_article = vader_pos_minus_neg_sentiment(article_text)
    nltk_compound_title = vader_compound_sentiment(title)
    nltk_compound_description = vader_compound_sentiment(description)
    nltk_compound_article = vader_compound_sentiment(article_text)
    tb_polarity_title = TextBlob(title).polarity
    tb_polarity_description = TextBlob(description).polarity
    tb_polarity_article = TextBlob(article_text).polarity
    stanza_sentiment_article = stanza_sentiment(article_text)

    return {"nltk_pos_minus_neg_title": nltk_pos_minus_neg_title,
            "nltk_pos_minus_neg_description": nltk_pos_minus_neg_description,
            "nltk_pos_minus_neg_article": nltk_pos_minus_neg_article,
            "nltk_compound_title": nltk_compound_title,
            "nltk_compound_description": nltk_compound_description,
            "nltk_compound_article": nltk_compound_article,
            "tb_polarity_title": tb_polarity_title,
            "tb_polarity_description": tb_polarity_description,
            "tb_polarity_article": tb_polarity_article,
            "stanza_sentiment_article": stanza_sentiment_article}


# filename = 'extreme_events_same_day_gnw_bw_stories.csv'
# url_gnw = 'http://www.globenewswire.com/news-release/2021/04/13/2209526/33039/en/ProQR-Announces-Publication-in-Nature-Medicine-for-Sepofarsen-in-Leber-Congenital-Amaurosis-10.html'
# url_bw = 'https://www.businesswire.com/news/home/20210413006168/en/U.S.-FDA-Grants-Accelerated-Approval-to-Trodelvy%C2%AE-for-the-Treatment-of-Metastatic-Urothelial-Cancer/'
# print(get_sentiments(
#     "U.S. FDA Grants Accelerated Approval to Trodelvy® for the Treatment of Metastatic Urothelial Cancer",
#     "OSTER CITY, Calif.--(BUSINESS WIRE)--Gilead Sciences, Inc. (Nasdaq: GILD) today announced that the U.S. Food and Drug Administration (FDA) has granted accelerated approval of Trodelvy® (sacituzumab govitecan-hziy) for use in adult patients with locally advanced or metastatic urothelial cancer (UC) who have previously received a platinum-containing chemotherapy and either a programmed death receptor-1 (PD-1) or a programmed death-ligand 1 (PD-L1) inhibitor. The accelerated approval was based on",
#     url_bw))

# pull_article(url_bw)

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
