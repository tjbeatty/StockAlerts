import csv


def organize_articles(filename_in):
    fda_stories = []
    investigations = []
    financial_stories = []
    executive_announcements = []
    other_stories = []
    fda_words = ['fda', 'phase 1', 'phase 2', 'phase 3', 'phase i', 'phase ii', 'phase iii', 'phase 0',
                 'pharmaceuticals', 'therapeutics', 'medical', 'biotech']
    financial_words = ['sales results', 'financials', 'provides update', 'business update', 'financial results',
                       'first quarter', 'second quarter', 'third quarter', 'fourth quarter', 'full year', 'year end',
                       'first-quarter', 'second-quarter', 'third-quarter', 'fourth-quarter', 'full-year', 'year-end',
                       'annual report', 'corporate update', 'year-to-date', 'fiscal year', 'results for q1',
                       'results for q2', 'results for q3', 'results for q4', 'results for the quarter']
    executive_words = ['ceo', 'cto', 'cfo', 'coo', 'chief', 'officer', 'board', 'president', 'director']
    announce_words = ['appoint', 'name', 'announce', 'promote', 'join', 'elect']
    investigation_words = ['investigation', 'investor', 'alert', 'shareholder notice', 'shareholder alert',
                           'law office']
    common_stock = ['Public Offering of Common Stock', 'direct offering of common stock',
                    'public offering of common shares', 'direct offering of common shares']
    present_words = ['to present', 'will present', 'presentation', 'participate']

    with open(filename_in, 'r') as csv_in:
        csv_reader = csv.reader(csv_in)
        header = next(csv_reader)

        for row in csv_reader:
            saved = 0
            [date, ticker, source, title, description, url, date_time_story, nltk_pos_minus_neg_title,
             nltk_pos_minus_neg_description, nltk_pos_minus_neg_article, nltk_compound_title, nltk_compound_description,
             nltk_compound_article, tb_polarity_title, tb_polarity_description, tb_polarity_article,
             stanza_sentiment_article, open_price, close_price, percent_change, max_percent_change, volume,
             average_volume] = row

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

        # header = ['date', 'ticker', 'pct_change_prev_close', 'day_percent_change', 'max_day_percent_change', 'source',
        #           'title', 'description', 'url', 'same_or_prev']

        story_lists = [fda_stories, investigations, financial_stories, executive_announcements, other_stories]
        story_types = ['fda_stories', 'investigations', 'financial_stories', 'executive_announcements', 'other_stories']
        filename_core = filename_in[:-4]

        for i, story_type in enumerate(story_types):

            filename_out = filename_core + '_' + story_type + '.csv'
            with open(filename_out, 'w') as csv_out:
                csv_writer = csv.writer(csv_out)
                csv_writer.writerow(header)

                for row in story_lists[i]:
                    csv_writer.writerow(row)




# file_list = ['financial_stories', 'investigations', 'executive_announcements', 'other_stories']
#
# for name in file_list:
#     retrieve_all_data_for_csv(name + '.csv', name + '_filtered_date.csv')

# retrieve_all_data_for_csv('csvs/other_stories_edit.csv', 'csvs/other_stories_filtered_date.csv')

# organize_articles('csvs/fda_bw_3000.csv')

