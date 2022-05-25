import pandas as pd
from tcn import TCN
import tensorflow as tf
import pickle
import os
import json

def read_json(file_path):
    f = open(file_path)
    return json.load(f)

def get_running_params(file_path):
    data = read_json(file_path)
    return data["max_iteration"], data["min_follower"]

def get_credentials(file_path):
    data = read_json(file_path)
    return data["bearer_token"], data["api_key"], data["api_key_secret"], data["access_token"], data["access_token_secret"]

def get_search_details(file_path):
    data = read_json(file_path)
    return data["controversial_topics"], data["trend_country_list"], data["starter_news_outlet"], data["trusted_news_outlet"], data["fake_news_accounts"]

def is_non_empty_file(file_path):
    return os.path.isfile(file_path) and os.path.getsize(file_path) > 0

def get_hashtag_list(hashtag_df):
    return hashtag_df.sort_values(by=['count'], ascending=False).hashtag[:100]

def get_user_list(user_df):
    return user_df.sort_values(by=['score']).id[:100]

def item_pos(item, in_memory_list):
    for i in range(len(in_memory_list)):
        if in_memory_list[i][0] == item:
            return i
    return -1

def item_df_pos(item, existing_list):
    for i in range(len(existing_list)):
        if existing_list[i] == item:
            return i
    return -1

# structure: user_id, screen_name, followers_count, score
def users_to_csv(file_path, user_list):
    output = []
    if is_non_empty_file(file_path):
        existing_user = pd.read_csv(file_path, lineterminator='\n')
        for user in user_list:
            df_pos = item_df_pos(user['id'], existing_user.id)
            if df_pos == -1:
                list_pos = item_pos(user['id'], output)

            if df_pos != -1:
                existing_user.loc[df_pos, 'score'] += user['score']
            elif list_pos != -1:
                output[list_pos][3] += user['score']
            else:
                output.append([user['id'], user['screen_name'], user['followers_count'], user['score']])
        dataframe = pd.DataFrame(output, columns=['id', 'screen_name', 'followers_count', 'score'])
        combined_dataframe = pd.concat([existing_user, dataframe])
        combined_dataframe.to_csv(file_path, index=False)
    else:
        for user in user_list:
            list_pos = item_pos(user['id'], output)
            if list_pos != -1:
                output[list_pos][3] += user['score']
            else:
                output.append([user['id'], user['screen_name'], user['followers_count'], user['score']])
        dataframe = pd.DataFrame(output, columns=['id', 'screen_name', 'followers_count', 'score'])
        dataframe.to_csv(file_path, index=False)
    return output

# structure: hashtag, count
def hashtags_to_csv(file_path, hashtag_list):
    output = []
    if is_non_empty_file(file_path):
        existing_hashtag = pd.read_csv(file_path, lineterminator='\n')
        for hashtag in hashtag_list:
            df_pos = item_df_pos(hashtag, existing_hashtag.hashtag)
            if df_pos == -1:
                list_pos = item_pos(hashtag, output)

            if df_pos != -1:
                existing_hashtag.loc[df_pos, 'count'] += 1
            elif list_pos != -1:
                output[list_pos][1] += 1
            else:
                output.append([hashtag, 1])
        dataframe = pd.DataFrame(output, columns=['hashtag', 'count'])
        combined_dataframe = pd.concat([existing_hashtag, dataframe])
        combined_dataframe.to_csv(file_path, index=False)
    else:
        for hashtag in hashtag_list:
            list_pos = item_pos(hashtag, output)
            if list_pos != -1:
                output[list_pos][1] += 1
            else:
                output.append([hashtag, 1])
        dataframe = pd.DataFrame(output, columns=['hashtag', 'count'])
        dataframe.to_csv(file_path, index=False)
    return output

# helps record screen name of the poster
def screen_name_helper(tweet):
    if tweet['original_user'] is not None:
        return tweet['original_user']['screen_name']
    else:
        if tweet['retweet_user'] is not None:
            return tweet['retweet_user']['screen_name']
        else:
            return "NotRecorded"

# structure: id, full_text, created_at, checked_at
def tweets_to_csv(file_path, tweet_collection):
    output = []
    if is_non_empty_file(file_path):
        existing_tweet = pd.read_csv(file_path, lineterminator='\n')
        for tweet in tweet_collection:
            if tweet['full_text'] not in existing_tweet.full_text.tolist():
                output.append([tweet['id'], tweet['full_text'], screen_name_helper(tweet), tweet['created_at'], tweet['checked_at']])

        dataframe = pd.DataFrame(output, columns=['id', 'full_text', 'posted_by', 'created_at', 'checked_at'])
        combined_dataframe = pd.concat([existing_tweet, dataframe])
        combined_dataframe.to_csv(file_path, index=False)
    else:
        for tweet in tweet_collection:
            output.append([tweet['id'], tweet['full_text'], screen_name_helper(tweet), tweet['created_at'], tweet['checked_at']])
        dataframe = pd.DataFrame(output, columns=['id', 'full_text', 'posted_by', 'created_at', 'checked_at'])
        dataframe.to_csv(file_path, index=False)
    return output

def load_model(file_path):
    return tf.keras.models.load_model(file_path, custom_objects={'TCN': TCN})
