from core_functions import *
import pandas as pd
import time
from util import *
import random
import sys
from transformers import AutoTokenizer

# authenticate helper
def auth(credential_file_path):
    bearer_token, api_key, api_key_secret, access_token, access_token_secret = get_credentials(credential_file_path)
    api_user = authenticate_as_user(api_key, api_key_secret, access_token, access_token_secret)
    api_app = authenticate_as_app(bearer_token)
    return api_user, api_app

def get_keywords():
    return [sys.argv[i] for i in range(1, len(sys.argv))]

# get list of hashtags
def get_hashtags(hashtag_file_path, keywords):
    if len(keywords) == 1 and keywords[0] == "ALL" and is_non_empty_file(hashtag_file_path):
        return get_hashtag_list(pd.read_csv(hashtag_file_path))
    else:
        return []

# get list of users
def get_users(user_file_path, starter_news_outlet, keywords):
    if len(keywords) == 1 and keywords[0] == "ALL":
        if is_non_empty_file(user_file_path):
            user_df = pd.read_csv(user_file_path)
            user_id_list = get_user_list(user_df)
        else:
            user_df = None
            user_id_list = starter_news_outlet
    else:
        user_df = None
        user_id_list = []
    return user_df, user_id_list

# get what to search
def get_searches(keywords):
    if len(keywords) == 1 and keywords[0] == "ALL":
        controversial_topics, trend_country_list, starter_news_outlet, trusted_news_outlet, fake_news_accounts = get_search_details('./config/to_search.json')
        tweet_file_name = 'tweets_info'
        para_per_query = 4
    else:
        controversial_topics, trend_country_list, starter_news_outlet, trusted_news_outlet, fake_news_accounts = get_search_details('./config/to_search.json')
        controversial_topics = keywords
        trend_country_list = []
        starter_news_outlet = []
        tweet_file_name = "_".join(keywords).lower()
        para_per_query = 1
    return controversial_topics, trend_country_list, starter_news_outlet, trusted_news_outlet, fake_news_accounts, tweet_file_name, para_per_query

# learn from real and fake sources
def model_learn(api_app, tokenizer, model, tweet_file_name, trusted_tweets_collection, fake_tweets_collection):
    tweet_collection = []
    for tweet in trusted_tweets_collection:
        tweet_collection.append((tweet, 1))
    for tweet in fake_tweets_collection:
        tweet_collection.append((tweet, 0))
    for tweet in fake_tweets_collection:
        tweet_collection.append((tweet, 0))
    print(len(tweet_collection))
    random.shuffle(tweet_collection)
    updated_model = learn(model, tokenizer, tweet_collection, tweet_file_name)
    return updated_model


# exit the program if no keyword is provided
if len(sys.argv) < 2:
    print("You need to specify what to search after the file name. You can either choose 'ALL' which searches everything from trending topics to controversial topics and so on. Or you can specify what you want to search, if there are more than one keyword, they should be seperated by a single space.")
    exit()

print("Program starts at " + str(time.strftime("%H:%M:%S", time.localtime())) + "\n")
# define some variables for later use
tweets_to_check = []
real_tweets_collected = []
fake_tweets_collected = []
sleep_time = 20
user_tweets_number = 20
search_tweets_number = 100
iterations_per_update_trend = 10
iterations_per_analysis = 5
current_iteration = 0
max_iteration, min_follower = get_running_params('./config/running_iterations.json')

# load tokenizer and model
tokenizer_bert = AutoTokenizer.from_pretrained("vinai/bertweet-base", use_fast=False)
tokenizer_bert.padding_side='right'
model = load_model("./models/tcn.h5")
# get the keyword(s) from command line argument
keywords = get_keywords()
# load search details
controversial_topics, trend_country_list, starter_news_outlet, trusted_news_outlet, fake_news_accounts, tweet_file_name, para_per_query = get_searches(keywords)
# authentication
api_user, api_app = auth('./config/credentials.json')
# get latest tweet's id as a starting point
since_id = start(api_user)
# the default running time of this program is set to around one hour (2 min each)
while current_iteration < max_iteration:
    time.sleep(sleep_time)
    print("iteration " + str(current_iteration + 1) + ":")
    if current_iteration % iterations_per_update_trend == 0:
        trends = get_popular_topics(api_app, trend_country_list)
    if current_iteration % iterations_per_analysis == 1 or current_iteration == 0:
        # get list of hashtags to check for
        hashtag_list = get_hashtags('./fake/hashtags.csv', keywords)
        # get the users to check for
        user_df, user_id_list = get_users('./users/users.csv', starter_news_outlet, keywords)
    # get the queries formed for searching
    search_queries = get_all_queries(controversial_topics, trends, hashtag_list, para_per_query)
    # get the tweets to check for, currently retrieve 100 per query and 20 per user
    tweets_collection = get_all_tweets(api_app, search_queries, search_tweets_number, since_id, user_tweets_number, user_id_list, min_follower)
    tweets_to_check.extend(tweets_collection)
    # get the tweets for incremental learning
    real_tweets_collected.extend(get_all_tweets(api_app, [], search_tweets_number, since_id, user_tweets_number, trusted_news_outlet, 0))
    fake_tweets_collected.extend(get_all_tweets(api_app, [], search_tweets_number, since_id, user_tweets_number, fake_news_accounts, 0))
    # update since_id to the latest found in the tweets retrieved
    since_id = update_since_id(tweets_collection, since_id)
    # analyse every 10 min
    if current_iteration % iterations_per_analysis == 0 and current_iteration != 0:
        # learning from trusted and fake sources to improve accuracy
        model = model_learn(api_app, tokenizer_bert, model, tweet_file_name, real_tweets_collected, fake_tweets_collected)
        # analyse and record the result
        result = analyse(model, tokenizer_bert, tweets_to_check, user_df, tweet_file_name)
        # clear lists
        tweets_to_check.clear()
        real_tweets_collected.clear()
        fake_tweets_collected.clear()
    current_iteration += 1

model.save("./models/tcn.h5")
print("Program ends at " + str(time.strftime("%H:%M:%S", time.localtime())))
print_run_result()
