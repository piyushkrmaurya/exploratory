import re
import os

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

_stopwords_file = open(os.path.join(__location__, "data/stopwords"), "r")
_stopwords = set(_stopwords_file.read().split())
_stopwords_file.close()


def remove_stopwords(tokens):
    return [token for token in tokens if str(token).lower() not in _stopwords]


def join(tokens):
    return " ".join([str(token) for token in tokens])


def str_list(tokens):
    return [str(token) for token in tokens]


pronoun_groups = [
    ["i", "me", "my", "mine", "myself"],
    ["we", "us", "our", "ours", "ourself"],
    ["you", "your", "yours", "yourself"],
    ["he", "him", "his", "himself"],
    ["she", "her", "herself"],
    ["it", "its", "itself"],
    ["they", "them", "their", "theirs", "themselves"],
]


def find_pronoun_group(token):
    for group in pronoun_groups:
        if str(token).lower() in group:
            return group
    return []


def check_pronoun_group(token1, token2):
    for group in pronoun_groups:
        if str(token1).lower() in group and str(token2).lower() in group:
            return True
    return False
