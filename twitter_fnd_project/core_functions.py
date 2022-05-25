# steps:
    # 1. authenticate and send tweet ✅
    # 2. get the trends ✅
    # 3. prepare params for search (don't use just one request) ✅
    # 4. form search queries ✅
        # trends, (use OR and exact match) ✅
        # hashtag, (use OR) ✅
        # controversial topics, (use OR) ✅
        # no replies ✅
    # 5. get tweets (consecutively) ✅
        # 5.1 get tweets about certain topics ✅
        # 5.2 get tweets from the user collected ✅
        # 5.3 store in memory and remove duplicates ✅
    # 6. process tweets ✅
        # categorise (three kinds) ✅
        # no personal opinions ✅
        # pre-process ✅
    # 7. analyse data ✅
        # calculate score ✅
        # apply bias ✅
    # 8. record and update data (write to file) ✅
        # record new data ✅
        # update existing data ✅
    # 9. incremental learning (if i can)
    # repeat process every five min ✅
    # demonstrate time


import tweepy
import pandas as pd
import numpy as np
from process_text import *
from util import *
from langdetect import detect
import time
from datetime import datetime,timezone

total_retrieved = []
total_learnt_fake = []
total_learnt_real = []
total_analysed_fake = []
total_analysed_real = []
total_recorded_fake = []
total_recorded_real = []

def authenticate_as_app(bearer_token):
    return tweepy.API(tweepy.OAuth2BearerHandler(bearer_token))

def authenticate_as_user(api_key, api_key_secret, access_token, access_token_secret):
    return tweepy.API(tweepy.OAuth1UserHandler(api_key, api_key_secret, access_token, access_token_secret))

def start(api):
    text = "test at " + str(time.strftime("%H:%M:%S", time.localtime()))
    s = api.update_status(text, trim_user=True)
    return s.id

def get_popular_topics(api, woeids):
    trends_list = []
    for woeid in woeids:
        trends = api.get_place_trends(woeid)
        for trend in trends[0]['trends'][:10]:
            if trend['name'] not in trends_list:
                trends_list.append(trend['name'])
    return trends_list

# combine popular and pre-defined controversial topics
def form_search_string(params, operator=" OR "):
    combined_string = ""
    for param in params:
        combined_string += param
        if param != params[-1]:
            combined_string += operator
    combined_string += " -filter:replies"
    return combined_string


def get_all_queries(controversial_topics, trends, hashtag_list, para_per_query):
    query_list = []
    topic_list = [topic.lower() for topic in controversial_topics]
    topic_index = 0

    for trend in trends:
        if trend.lower() not in topic_list:
            if "#" not in trend:
                trend_name = '"' + trend.lower() + '"'
            else:
                trend_name = trend.lower()
            topic_list.append(trend_name)

    for hashtag in hashtag_list:
        topic_list.append(hashtag)

    number_of_topics = len(topic_list)
    while topic_index != number_of_topics:
        if number_of_topics >= (topic_index + para_per_query):
            query_list.append(form_search_string(topic_list[topic_index:topic_index+para_per_query]))
            topic_index += para_per_query
        else:
            query_list.append(form_search_string(topic_list[topic_index:number_of_topics]))
            topic_index += (number_of_topics - topic_index)
    return query_list


def get_tweets(api, search_string, count, since_id, lang='en', result_type='mixed', tweet_mode='extended'):
    try:
        searched_tweets = api.search_tweets(q=search_string, lang=lang, result_type=result_type, count=count, since_id=since_id, tweet_mode=tweet_mode)
    except:
        searched_tweets = []
    return searched_tweets


def get_user_tweet(api, user_id, since_id, count, exclude_replies=True, include_rts=True, tweet_mode='extended'):
    try:
        user_tweets = api.user_timeline(user_id=user_id, since_id=since_id, count=count, exclude_replies=exclude_replies, include_rts=include_rts, tweet_mode=tweet_mode)
    except:
        user_tweets = []
    return user_tweets

# check if the text is a personal opinion
def is_personal_opinion(text):
    text_list = text.replace("’", "'").lower().split(" ")
    if len(text_list) <= 10 or "?" in text:
        return True

    for word in text_list:
        if "breaking" == word or "news" == word:
            return False
    # personal terms like I and you, etc, words that would typically not appear in news
    personal_words = [
        "i", "me", "my", "mine", "i'd", "i'm", "i've", "imma", "we", "gonna", "you", "u", "your", "yours", "you'd", "you've", "you're", "ya", "personally", "think", "thinking", "thought", "reckon", "believe", "suppose", "opinion", "definitely", "absolutely", "=", "hate", "love", "probably", "should", "might", "let's", "live:", "why"
    ]
    for word in text_list:
        if word in personal_words:
            return True

    return False


def form_user_dict(user):
    user_dict = {
        "id": user.id,
        "screen_name": user.screen_name,
        "followers_count": user.followers_count,
        "score": 0
    }
    return user_dict

def add_tweets(tweet_df, tweet_collection, overall_tweet_collection, tweet_text_collection, min_follower):
    for tweet in tweet_collection:
        if tweet.user.followers_count < min_follower:
            continue

        if hasattr(tweet, 'retweeted_status'):
            text = tweet.retweeted_status.full_text
            if (tweet_df is not None and text in tweet_df.full_text.tolist()) or tweet.retweeted_status.user.followers_count < min_follower:
                retweet_user_dict = None
            else:
                retweet_user_dict = form_user_dict(tweet.retweeted_status.user)
            original_user_dict = form_user_dict(tweet.user)
        elif hasattr(tweet, 'quoted_status'):
            text = tweet.quoted_status.full_text
            if (tweet_df is not None and text in tweet_df.full_text.tolist()) or tweet.quoted_status.user.followers_count < min_follower:
                retweet_user_dict = None
            else:
                retweet_user_dict = form_user_dict(tweet.quoted_status.user)
            original_user_dict = None
        else:
            text = tweet.full_text
            retweet_user_dict = None
            original_user_dict = form_user_dict(tweet.user)

        if len(text.replace("’", "'").lower().split(" ")) <= 5:
            continue

        if is_personal_opinion(text) and min_follower != 0:
            continue

        # tuple structure: (id, created_at, full_text, hashtag_used, retweet_user, original_user, checked_at)
        tweet_dict = {
            "id": tweet.id,
            "created_at": tweet.created_at,
            "full_text": text,
            "hashtag_used": [ ("#" + hashtag['text'].lower()) for hashtag in tweet.entities['hashtags']],
            "retweet_user": retweet_user_dict,
            "original_user": original_user_dict,
            "checked_at": None
        }

        try:
            is_eng = detect(text) == 'en'
        except:
            continue
        if is_eng:
            if min_follower == 0:
                overall_tweet_collection.append(tweet_dict)
                tweet_text_collection.append(text)
            else:
                if text not in tweet_text_collection:
                    overall_tweet_collection.append(tweet_dict)
                    tweet_text_collection.append(text)

def get_combined_tweet_df():
    real_file_path = './real/tweets_info.csv'
    fake_file_path = './fake/tweets_info.csv'
    if is_non_empty_file(real_file_path) and is_non_empty_file(fake_file_path):
        return pd.concat([pd.read_csv(real_file_path, lineterminator='\n'), pd.read_csv(fake_file_path, lineterminator='\n')])
    elif is_non_empty_file(real_file_path):
        return pd.read_csv(real_file_path, lineterminator='\n')
    elif is_non_empty_file(fake_file_path):
        return pd.read_csv(fake_file_path, lineterminator='\n')
    else:
        return None

def get_all_tweets(api, queries, search_count, since_id, user_max_count, user_id_list, min_follower):
    overall_tweet_collection = []
    tweet_text_collection = []
    tweet_df = get_combined_tweet_df()

    tweet_count = 0
    tweet_count_collection = []

    for query in queries:
        tweet_collection = get_tweets(api, query, search_count, since_id)
        tweet_count += len(tweet_collection)
        tweet_count_collection.append(len(tweet_collection))
        add_tweets(tweet_df, tweet_collection, overall_tweet_collection, tweet_text_collection, min_follower)

    # the user part of the tweets
    for user_id in user_id_list:
        user_tweet_collection = get_user_tweet(api, user_id, since_id, user_max_count)
        tweet_count += len(user_tweet_collection)
        tweet_count_collection.append(len(user_tweet_collection))
        add_tweets(tweet_df, user_tweet_collection, overall_tweet_collection, tweet_text_collection, min_follower)

    print("number of tweets retrieved:" + str(tweet_count))
    total_retrieved.append(tweet_count)
    print(tweet_count_collection)
    print()
    return overall_tweet_collection


def update_since_id(tweets_collection, old_since_id):
    new_since_id = old_since_id
    for tweet in tweets_collection:
        if tweet['id'] > new_since_id:
            new_since_id = tweet['id']
    return new_since_id


# apply bias to the existing user
def apply_bias(user_id, user_df, original_score, bias):
    if user_df is not None:
        item_pos = item_df_pos(user_id, user_df.id)
        if item_pos != -1:
            previous_score = user_df.loc[item_pos, 'score']
            return original_score * (1 + bias) ** previous_score
    return original_score


# record information to files
def record_info(tweet_collection, real_tweet, fake_tweet, fake_hashtag_list, user_list, tweet_file_name, mode):
    output_real_tweet = tweets_to_csv('./real/' + tweet_file_name + '.csv', real_tweet)
    output_fake_tweet = tweets_to_csv('./fake/' + tweet_file_name + '.csv', fake_tweet)
    output_fake_hashtag = hashtags_to_csv('./fake/hashtags.csv', fake_hashtag_list)
    output_user = users_to_csv('./users/users.csv', user_list)

    total_recorded_fake.append(len(output_fake_tweet))
    total_recorded_real.append(len(output_real_tweet))

    if mode == 'l':
        print("A total of " + str(len(tweet_collection)) + " tweets were learnt since last time learnt. Out of which " + str(len(real_tweet)) + " of them were real and " + str(len(fake_tweet)) + " were fake.")
    else:
        print("A total of " + str(len(tweet_collection)) + " tweets were analysed since last time analysed. Out of all the tweets analysed, " + str(len(real_tweet)) + " of them are real and " + str(len(fake_tweet)) + " of them are fake. " + str(len(output_real_tweet)) + " real tweets and " + str(len(output_fake_tweet)) + " fake tweets were recorded since they were not already recorded. A list of " + str(len(fake_hashtag_list)) + " hashtags were used in fake tweets in total.\n")

# do the prediction and record results
def analyse(model, tokenizer, tweet_collection, user_df, tweet_file_name):
    if len(tweet_collection) == 0:
        return "No tweet was retrieved in this batch :("

    real_tweet = []
    fake_tweet = []
    fake_hashtag_list = []
    user_list = []

    for tweet in tweet_collection:
        tweet['checked_at'] = datetime.now(timezone.utc)
        tokenized_text_bert = tokenise_bert([tweet['full_text']], tokenizer)
        prediction_score = model.predict(tokenized_text_bert)[0][0]
        if tweet['original_user'] != None:
            final_score = apply_bias(tweet['original_user']['id'], user_df, prediction_score, 0.01)
        else:
            final_score = prediction_score

        if final_score >= 0.5:
            real_tweet.append(tweet)
            score = 1
        else:
            fake_tweet.append(tweet)
            fake_hashtag_list.extend(tweet['hashtag_used'])
            score = -1

        if tweet['retweet_user'] is not None:
            tweet['retweet_user']['score'] = score
            user_list.append(tweet['retweet_user'])
        if tweet['original_user'] is not None:
            tweet['original_user']['score'] = score
            user_list.append(tweet['original_user'])

    record_info(tweet_collection, real_tweet, fake_tweet, fake_hashtag_list, user_list, tweet_file_name, 'c')
    total_analysed_fake.append(len(fake_tweet))
    total_analysed_real.append(len(real_tweet))
    return (real_tweet, fake_tweet)


def learn(model, tokenizer, tweet_collection, tweet_file_name, epochs=15, lr=0.0001):
    if len(tweet_collection) == 0:
        print("No learning in this iteration :(")
        return model

    real_tweet = []
    fake_tweet = []
    X_train = []
    y_train = []
    print(len(tweet_collection))
    for tweet_tuple in tweet_collection:
        tweet = tweet_tuple[0]
        label = tweet_tuple[1]
        tweet['checked_at'] = datetime.now(timezone.utc)
        if label == 1:
            real_tweet.append(tweet)
        else:
            fake_tweet.append(tweet)
        X_train.append(tweet['full_text'])
        y_train.append(label)
    X_train = np.array(tokenise_bert(X_train, tokenizer))
    y_train = np.array(y_train)

    print(len(fake_tweet))
    print(len(real_tweet))
    total_learnt_fake.append(len(fake_tweet))
    total_learnt_real.append(len(real_tweet))
    record_info(tweet_collection, real_tweet, fake_tweet, [], [], tweet_file_name, 'l')

    model.compile(loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
                  optimizer=tf.keras.optimizers.Adam(lr),
                  metrics=['accuracy'])
    model.fit(X_train, y_train, epochs=epochs, batch_size=32, shuffle=True)
    return model

def print_run_result():
    print("In this run,")
    print("Total number of tweets retrieved: " + str(sum(total_retrieved)))
    print("Total number of fake tweet learnt: " + str(sum(total_learnt_fake)))
    print("Total number of real tweet learnt: " + str(sum(total_learnt_real)))
    print("Total number of fake tweets found: " + str(sum(total_analysed_fake)))
    print("Total number of real tweets found: " + str(sum(total_analysed_real)))
    print("Total number of fake tweets recorded: " + str(sum(total_recorded_fake)))
    print("Total number of real tweets recorded: " + str(sum(total_recorded_real)))
