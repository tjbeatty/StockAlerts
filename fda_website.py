import csv
import urllib.request
from time import sleep
from stocks_info import *


# Retrieve the company name form the FDA approvals page for a single approval
def retrieve_comp_name_from_fda(url):
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')
    appl_details = soup.find_all(attrs={'class': 'appl-details-top'})

    try:
        company = appl_details[1].text.strip().lower()
    except IndexError:
        company = ''

    return company


# Retrieve the company names for all fda approvals in a table
# NOTE: I should change this to pull straight from the url, not form a csv of copy/pasted tables
def retrieve_all_comp_name_from_fda():
    output = []
    with open('fda_approvals_list.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        header = next(csv_reader)

        for row in csv_reader:
            [drug, active_ingredient, url, date] = row

            company = retrieve_comp_name_from_fda(url)

            row.append(company)
            output.append(row)

    header = ['drug', 'active_ingredient', 'url', 'date', 'company_fda_name']
    with open('fda_approvals_w_company.csv', 'w') as csvout:
        csv_writer = csv.writer(csvout)
        csv_writer.writerow(header)
        csv_writer.writerows(output)


def retrieve_all_ticker_symbols_from_fda(file):
    output = []

    replace_dict = {'inc': '', 'theraps': 'therap', 'hlthcare': 'healthcare'}
    with open(file, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        header = next(csv_reader)

        for row in csv_reader:
            [drug, active_ingredient, url, date, company_name_fda] = row

            # Clean up some common truncations from FDA
            company_name_fda_clean = ' '.join(replace_dict.get(ele, ele) for ele in company_name_fda.split())

            [ticker, company_name, exchange, flag] = retrieve_ticker_from_name(company_name_fda_clean)
            row.extend([ticker, company_name, exchange, flag])
            output.append(row)

    header = ['drug', 'active_ingredient', 'fda_url', 'date', 'fda_name', 'ticker', 'company_name', 'exchange', 'flag']
    with open('fda_approvals_w_company_ticker.csv', 'w') as csvout:
        csv_writer = csv.writer(csvout)
        csv_writer.writerow(header)
        csv_writer.writerows(output)


def get_price_change_fda_all_approval_dates():
    output = []
    with open('fda_approvals_w_company_ticker_manual_check.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        header = next(csv_reader)

        for row in csv_reader:
            [drug, active_ingredient, url, approval_date, fda_name, ticker, company_name, exchange, flag] = row

            if ticker != '' and exchange != 'OTC':
                price_change = get_percent_change_from_date_polygon(ticker, approval_date)
                output.append([company_name, drug, approval_date, ticker, price_change])

                # Added to throttle to 5 API calls per minute
                sleep(13)

    header = ['company_name', 'drug', 'approval_date', 'ticker', 'price_change']
    with open('fda_approval_price_change.csv', 'w') as csvout:
        csv_writer = csv.writer(csvout)
        csv_writer.writerow(header)
        csv_writer.writerows(output)