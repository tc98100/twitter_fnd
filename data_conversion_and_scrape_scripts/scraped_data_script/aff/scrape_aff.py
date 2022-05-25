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
    statement_quote = soup.find_all('div', attrs={'class':'post-content'}) #Get the tag and it's class

    #Loop through the div m-statement__quote to get the link
    for i in statement_quote:
        link2 = i.find_all('a')
        statements.append(link2[0].text.strip())


#Loop through 'n-1' webpages to scrape the data
for i in range(1, 977):
    scrape_website('https://americasfreedomfighters.com/page/'+str(i))
print("finished 1")

for i in range(1, 45):
    scrape_website('https://americasfreedomfighters.com/category/2a-rights-2/page/'+str(i))
print("finished 2")

for i in range(1, 973):
    scrape_website('https://americasfreedomfighters.com/category/politics/page/'+str(i))
print("finished 3")

#Create a new dataFrame
data = pd.DataFrame(columns = ['title', 'class'])
data['title'] = statements
data['class'] = 0
#Show the data set
# print(data)
data.drop_duplicates(subset='title', ignore_index=True)
data.to_csv('aff-scrape-full.csv', index=False, sep=',')
