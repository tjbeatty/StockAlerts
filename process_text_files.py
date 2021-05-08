import pandas as pd
import numpy as np
from stocks_info import get_shares_outstanding
import csv

filename_core = 'csvs/fda_bw_10000'
filename_in = filename_core + '.csv'
filename_final = filename_core + '_final.csv'

# Read file in as dataframe
df = pd.read_csv(filename_in)
# Remove duplicates
df = pd.DataFrame.drop_duplicates(df)
# Remove "City, State (NEWS AGENCY) --" beginning of the description
df['description'] = df['description'].str.replace('.*\) ?--', '')
# Remove opening blank spaces
df['description'] = df['description'].replace(to_replace='^\s+', value='', regex=True)
# Remove most ticker tags
df['description'] = df['description'].replace(to_replace=' \(\w{3,7}\:.{1,6}\)', value='', regex=True)
# Replace multiple spaces with a single space
df['description'] = df['description'].replace(to_replace='\s+', value=' ', regex=True)
df['title'] = df['title'].replace(to_replace='\s+', value=' ', regex=True)

df.to_csv(filename_final, index=False)
