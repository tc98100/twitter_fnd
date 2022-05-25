#Import the dependencies
from bs4 import BeautifulSoup
import pandas as pd
import requests
import urllib.request
import time

#Create lists to store the scraped data
statements = []

#Create a function to scrape the site
def scrape_website(URL):
    webpage = requests.get(URL)  #Make a request to the website
    soup = BeautifulSoup(webpage.text, "html.parser") #Parse the text from the website
    #Get the tags and it's class
    statement_quote = soup.find_all('a', attrs={'class':'stretched-link'}) #Get the tag and it's class
    real_len = len(statement_quote) - 5
    statement_quote = statement_quote[:real_len]
    #Loop through the div m-statement__quote to get the link
    for i in statement_quote:
        link2 = i.find_all('span')
        if len(link2[0].text.split()) > 5:
            statements.append(link2[0].text.strip())

search_list = [['mostly-false', 60], ['false', 496], ['labeled-satire', 35], ['originated-as-satire', 3], ['miscaptioned', 49], ['mixture', 120]]

#Loop through 'n-1' webpages to scrape the data
for search in search_list:
    for i in range(1, search[1]):
        url = 'https://www.snopes.com/fact-check/rating/' + search[0] + '/page/' + str(i)
        scrape_website(url)

#Create a new dataFrame
data = pd.DataFrame(columns = ['title', 'class'])
data['title'] = statements
data['class'] = 0
data.drop_duplicates(subset='title', ignore_index=True)
data.to_csv('snopes-scrape-full.csv', index=False, sep=',')
