from selenium.webdriver.common.by import By
import csv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import business_wire
import datetime
import stocks_info
from time import sleep


def convert_date_for_api(date_string):
    date_object = datetime.datetime.strptime(date_string, '%B %d, %Y')
    date_out = date_object.strftime('%m/%d/%Y')
    return date_out


def retrieve_old_bus_wire_news(search_term, pages):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    browser = webdriver.Chrome(options=options)
    timeout = 20

    # Initialize the file output (write the header)
    header = ['date', 'title', 'description']
    csv_name = search_term + '_historical_business_wire_stories.csv'

    # Remove file if it already exists
    if os.path.exists(csv_name):
        os.remove(csv_name)

    with open(csv_name, 'w') as csvout:
        csv_writer = csv.writer(csvout)
        csv_writer.writerow(header)

    for page in range(1, pages+1):
        print("Now on page #" + str(page) + "...")
        url = 'https://www.businesswire.com/portal/site/home/search/?searchType=news&searchTerm=' \
              + search_term + '&searchPage=' + str(page)
        browser.get(url)

        try:
            # Wait until the bottom image element loads before reading in data.
            WebDriverWait(browser, timeout).\
                until(EC.visibility_of_element_located((By.XPATH, '//*[@id="bw-group-all"]/div/div/div[3]/'
                                                                  'section/ul/li[10]/p')))
            # Retrieve dates from each story
            date_elems = browser.find_elements_by_xpath('//*[@id="bw-group-all"]/div/div/div[3]/section/'
                                                        'ul/li[*]/div[1]/time')
            # Retrieve title from each story
            title_elems = browser.find_elements_by_xpath('//*[@id="bw-group-all"]/div/div/div[3]/section/ul/li[*]/h3/a')
            # Retrieve description from each story
            heading_elems = browser.find_elements_by_xpath('//*[@id="bw-group-all"]/div/div/div[3]/section/ul/li[*]/p')

            # Take text from each object
            date_text = [x.text for x in date_elems]
            title_text = [x.text for x in title_elems]
            heading_text = [x.text for x in heading_elems]

            # Write the current page of results to the output file
            with open(csv_name, 'a+') as csvout:
                for i, n in enumerate(date_text):
                    output = [date_text[i], title_text[i], heading_text[i]]
                    csv_writer = csv.writer(csvout)
                    csv_writer.writerow(output)

        except TimeoutException:
            print("Timed out waiting to load")

    browser.quit()


def pull_daily_change_for_all_bus_wire_articles(csv_input, csv_output):
    header = ['date', 'title', 'description', 'percent_change', 'max_percent_change', 'volume']
    output = []
    with open(csv_input, 'r') as csv_in:
        csv_reader = csv.reader(csv_in)
        header_throwaway = next(csv_reader)
        with open(csv_output, 'w') as csv_out:
            csv_writer = csv.writer(csv_out)
            csv_writer.writerow(header)

            for row in csv_reader:
                [date, title, description] = row
                ticker = business_wire.find_ticker_in_description(description)
                if ticker:
                    print(ticker)
                    date_str = convert_date_for_api(date)
                    print(date_str)
                    stock_day_data = stocks_info.get_percent_change_from_date_iex(ticker, date_str)
                    if stock_day_data:
                        volume = stock_day_data['volume']
                        percent_change = stock_day_data['percent_change']
                        max_percent_change = stock_day_data['max_percent_change']
                        row.extend([percent_change, max_percent_change, volume])
                        csv_writer.writerow(row)


# retrieve_old_bus_wire_news('FDA', 2000)
# pull_daily_change_for_all_bus_wire_articles('fda_test.csv')


pull_daily_change_for_all_bus_wire_articles('FDA_check.csv',
                                            'FDA_percent_change2.csv')
