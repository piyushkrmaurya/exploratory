import json
import sys
import os
from . import tokenizer
from decimal import Decimal

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def get_probability():
    with open(
        os.path.join(__location__, "data/pos_tagger_probability.json"),
        "r",
        encoding="utf8",
    ) as f:
        probability = json.load(f)
    f.close()

    emission_probability = probability["emission"]
    transition_probability = probability["transition"]

    return transition_probability, emission_probability


def pos_tag(sentence=None, tokenized=True):

    if not sentence:
        sentence = input()
        sentence = tokenizer.tokenize(sentence)

    if not tokenized:
        sentence = tokenizer.tokenize(sentence)
    transition_probability, emission_probability = get_probability()

    dp = [{"<start>": (1, "")}]
    word_counter = 0
    for word in sentence:
        dp.append({})
        word = word.lower()

        if word not in emission_probability:
            word = "<unknown>"

        for tag2 in emission_probability[word]:
            max_probability = 0
            for tag1 in dp[word_counter]:
                prior_probability = dp[word_counter][tag1][0]
                cur_probability = Decimal(
                    Decimal(prior_probability)
                    * Decimal(transition_probability[tag2][tag1])
                    * Decimal(emission_probability[word][tag2])
                )
                if cur_probability > max_probability:
                    max_probability = cur_probability
                    max_tag = tag1
            dp[word_counter + 1][tag2] = (max_probability, max_tag)
        word_counter += 1

    max_probability = 0
    dp.append({})
    for tag in dp[word_counter]:
        prior_probability = dp[word_counter][tag][0]
        cur_probability = Decimal(
            Decimal(prior_probability) * Decimal(transition_probability["<end>"][tag])
        )
        if cur_probability > max_probability:
            max_probability = cur_probability
            max_tag = tag
    dp[word_counter + 1]["<end>"] = (max_probability, max_tag)
    word_counter += 1

    tag_list = []
    last_tag = "<end>"
    while word_counter > 1:
        last_tag = dp[word_counter][last_tag][1]
        tag_list.append(last_tag)
        word_counter -= 1

    output_tags = list(reversed(tag_list))

    return output_tags


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(pos_tag(sys.argv[1]))
    else:
        print(pos_tag())
