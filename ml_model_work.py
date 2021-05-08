import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from spacy.lang.en.stop_words import STOP_WORDS
from spacy.lang.en import English
import string
import pickle
from sklearn.metrics import log_loss, roc_auc_score, recall_score, precision_score, average_precision_score, f1_score, classification_report, accuracy_score, plot_roc_curve, plot_precision_recall_curve, plot_confusion_matrix


def spacy_tokenizer(utterance):
    punctuations = string.punctuation
    parser = English()
    stopwords = list(STOP_WORDS)
    tokens = parser(utterance)
    return [token.lemma_.lower().strip() for token in tokens
            if token.text.lower().strip() not in stopwords and token.text not in punctuations]


df = pd.read_csv('csvs/fda_fda_stories_merged.csv')

# Break up data into x and y
df2 = df[['description', 'percent_change']]
df2['change_bucket'] = pd.cut(df['percent_change'], bins=[-1000, -.05, .05, 1000], right=True, labels=False) + 1

description = df2['description'].values
change_bucket = df2['change_bucket'].values

# Break up data into training and testing set

random_seed = 1000
training_data, testing_data, y_train, y_test = \
    train_test_split(description, change_bucket, test_size=0.2, random_state=random_seed)

# vectorizer = CountVectorizer(tokenizer=spacy_tokenizer, ngram_range=(1,5))
#
# vectorizer.fit(training_data)

# X_train = vectorizer.transform(training_data)
# X_test = vectorizer.transform(testing_data)
#
# pickle.dump(X_test, open('X_test.pkl', 'wb'))
# pickle.dump(X_train, open('X_train.pkl', 'wb'))
# pickle.dump(y_test, open('y_test.pkl', 'wb'))
# pickle.dump(y_train, open('y_train.pkl', 'wb'))
# X_train_file = 'X_train.pkl'
# X_train = pickle.load(open(X_train_file, 'rb'))

# Had to increase the max iterations to circumvent an error
# classifier = LogisticRegression(max_iter=1000)
# classifier.fit(X_train, y_train)
# model = classifier

# # Save the model to a file
model_file = 'fda_fda_stories_model_2_lbfgs.sav'
# pickle.dump(classifier, open(model_file, 'wb'))

X_test_file = 'X_test.pkl'
y_test_file = 'y_test.pkl'
X_test = pickle.load(open(X_test_file, 'rb'))
y_test = pickle.load(open(y_test_file, 'rb'))
model = pickle.load(open(model_file, 'rb'))

accuracy = model.score(X_test.toarray(), y_test)
print("Accuracy:", accuracy)

predictions = model.predict(X_test.toarray())

print(type(predictions))
print(type(testing_data))
print(type(y_test))
df3 = pd.DataFrame([testing_data, y_test, predictions], index=['description', 'bucket', 'prediction']).transpose()

df3 = df3.loc[(df3.bucket == 3) & (df3.prediction == 3)]
print(df3)
df3.to_csv('good_predicts.csv', index=False)

# plot_confusion_matrix(model, X_test, y_test)
# plt.show()