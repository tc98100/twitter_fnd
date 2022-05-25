#Import the dependencies
from bs4 import BeautifulSoup
import pandas as pd
import requests
import urllib.request
import time
from urllib.request import Request, urlopen

class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0"

#Create lists to store the scraped data
statements = []

#Create a function to scrape the site
def scrape_website(URL):
    req = Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read().decode('utf-8')  #Make a request to the website
    soup = BeautifulSoup(webpage, "html.parser") #Parse the text from the website
    #Get the tags and it's class
    statement_quote = soup.find_all('h2', attrs={'class':'entry-title'}) #Get the tag and it's class

    #Loop through the div m-statement__quote to get the link
    for i in statement_quote:
        link2 = i.find_all('a')
        text = link2[0].text.split(":")[1].strip()
        if len(text) > 5:
            statements.append(text)


#Loop through 'n-1' webpages to scrape the data
for i in range(1, 1183):
    if i%100 == 0:
        print("reached x00")
    scrape_website('https://www.poynter.org/ifcn-covid-19-misinformation/page/'+str(i))

#Create a new dataFrame
data = pd.DataFrame(columns = ['title', 'class'])
data['title'] = statements
data['class'] = 0
#Show the data set
# print(data)
data.drop_duplicates(subset='title', ignore_index=True)
data.to_csv('ifcn-scrape-full.csv', index=False, sep=',')
