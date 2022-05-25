import nltk
from nltk.corpus import wordnet
from nltk.corpus import stopwords
from nltk.tokenize import TweetTokenizer
from nltk.stem import WordNetLemmatizer
import tensorflow as tf
import pickle
import re

stop_words = set(stopwords.words('english'))
stop_words.remove("not")
keep_list = ["aren't", "don't", "didn't", "hasn't", "wouldn't", "weren't", "not", "isn't", "couldn't",
             "shouldn't", "won't", "mustn't", "wasn't", "haven't", "doesn't", "hadn't", "needn't",
             "didn", "wasn", "isn", "hasn", "needn", "shouldn", "couldn", "wouldn", "weren", "haven", "aren", "doesn", "mustn", "mightn"]
tweet_tokenizer = TweetTokenizer(reduce_len=True)
wordnet_lemmatizer = WordNetLemmatizer()
tag_dict = {"J": wordnet.ADJ, "N": wordnet.NOUN, "V": wordnet.VERB, "R": wordnet.ADV}

def get_pos_tag(word):
    return tag_dict.get(nltk.pos_tag([word])[0][1][0].upper(), wordnet.NOUN)

def seperate_texts(text):
    return tweet_tokenizer.tokenize(text)

def lemmatize_nots(text):
    for word in keep_list:
        text = text.replace(word, "not")
    return text

def lemmatize(word_list):
    return [wordnet_lemmatizer.lemmatize(word, get_pos_tag(word)) for word in word_list]

def remove_stopwords_and_others(word_list):
    return [word for word in word_list if word not in stop_words and "http" not in word and "@" not in word]

def process(text):
    text = lemmatize_nots(text)
    word_list = seperate_texts(text)
    result = remove_stopwords_and_others(word_list)
    lemmatized_result = lemmatize(result)
    data = " ". join(lemmatized_result)
    return data

def pre_process(data):
    result = []
    for text in data:
        text = text.lower()
        text = re.sub("'", ' ', text)
        text = process(text)
        text = re.sub("\\W", ' ', text)
        # get rid of extra spaces
        text = re.sub(' +', ' ', text)
        text = re.sub('^ ', '', text)
        text = re.sub(' $', '', text)
        result.append(text)
    return result

# def tokenise(features, tokenizer):
#     features = pre_process(features)
#     features = tokenizer.texts_to_sequences(features)
#     features = tf.keras.preprocessing.sequence.pad_sequences(features, padding='post', truncating='post', maxlen=64)
#     return features

def tokenise_bert(features, tokenizer):
    f = []
    features = pre_process(features)
    for feature in features:
        f.append(tokenizer.encode(feature, max_length=64, padding='max_length', truncation=True))
    return f
