import pandas as pd

df = pd.read_csv("./aff-scrape-full.csv")

banned = ['breaking', 'news']
f = lambda x: ' '.join([item for item in x.split() if item.lower() not in banned])
df["title"] = df["title"].apply(f)

# df.loc[df['title'].str.count(" ").gt(5)]

df = df[df.title.str.count(' ').gt(5)]

df.to_csv('aff-scrape-full-processed.csv', index=False, sep=',')
