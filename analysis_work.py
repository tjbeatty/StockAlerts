import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

filename_in = 'csvs/fda_gnw_3000.csv'

data = pd.read_csv(filename_in)

# data_clean = data[['date', 'ticker', 'source', 'url', 'title', 'date_time_story', 'description',
#                    'nltk_pos_minus_neg_title', 'nltk_pos_minus_neg_description', 'nltk_pos_minus_neg_article',
#                    'nltk_compound_title', 'nltk_compound_description', 'nltk_compound_article', 'tb_polarity_title',
#                    'tb_polarity_description', 'tb_polarity_article', 'stanza_sentiment_article', 'open_price',
#                    'close_price', 'percent_change', 'max_percent_change', 'volume', 'average_volume']]

data_clean = data[['nltk_pos_minus_neg_title', 'nltk_pos_minus_neg_description', 'nltk_pos_minus_neg_article',
                   'nltk_compound_title', 'nltk_compound_description', 'nltk_compound_article', 'tb_polarity_title',
                   'tb_polarity_description', 'tb_polarity_article', 'stanza_sentiment_article', 'percent_change',
                   'volume', 'average_volume']]



# sns.heatmap(data_clean.corr(), annot=True)
plt.scatter(data_clean['percent_change'], data_clean['tb_polarity_article'])

plt.show()
