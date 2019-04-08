import json
import pandas as pd
from decimal import Decimal


def dict_increase(d, k, v):
    temp_dict = d
    if k in temp_dict:
        temp_dict[k] += v
    else:
        temp_dict[k] = v
    return temp_dict


def named_enitites(test_words, transition_probability, emission_probability):

    output_test_tags = []

    for sentence in test_words:
        dp = [{"O": (1, "")}]
        word_counter = 0
        for word in sentence:
            dp.append({})

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
                Decimal(prior_probability) * Decimal(transition_probability["O"][tag1])
            )
            if cur_probability > max_probability:
                max_probability = cur_probability
                max_tag = tag
        dp[word_counter + 1]["O"] = (max_probability, max_tag)
        word_counter += 1

        tag_list = []
        last_tag = "O"
        while word_counter > 1:
            try:
                last_tag = dp[word_counter][last_tag][1]
            except:
                print(dp)
            tag_list.append(last_tag)
            word_counter -= 1

        output_test_tags.append(list(reversed(tag_list)))

    return output_test_tags


def test(predicted_tags):
    with open("data/ner_dataset.csv", "r", encoding="utf8") as f:
        dataset = f.read()
    f.close()
    words = []
    tags = []
    lw = []
    lt = []
    for tagged in dataset.split("\n\n"):
        for w_t in tagged.split("\n"):
            print(w_t)
            w, x, t = w_t.rsplit(",", 2)
            lw.append(w)
            lt.append(t)
        words.append(lw)
        tags.append(lt)
        lw = []
        lt = []

    correct = 0
    total = 0
    flattened_actual_tags = []
    flattened_predicted_tags = []
    for i in range(len(tags)):
        x = tags[i]
        y = predicted_tags[i]
        flattened_actual_tags += x
        flattened_predicted_tags += y
    correct = 0.0
    for i in range(len(flattened_predicted_tags)):
        if flattened_predicted_tags[i] == flattened_actual_tags[i]:
            correct += 1.0
        else:
            print(flattened_predicted_tags[i], flattened_actual_tags[i])
    print("Accuracy = " + str(100 * correct / len(flattened_predicted_tags)) + "%")


def run():

    with open("data/ner_dataset.csv", "r", encoding="utf8") as f:
        dataset = f.read()
    f.close()

    words = []
    l = []
    for tagged in dataset.split("\n\n"):
        for w_t in tagged.split("\n"):
            w, x, t = w_t.rsplit(",", 2)
            l.append(w)
        words.append(l)
        l = []

    with open("data/ner_probability.json", "r", encoding="utf8") as f:
        probability = json.load(f)
    f.close()

    emission_probability = probability["emission"]
    transition_probability = probability["transition"]

    test_tags = named_enitites(words, transition_probability, emission_probability)

    test(test_tags)

    # f = open("output", "w")
    # for i in range(len(words)):
    #     sentence = words[i]
    #     predicted_tags = test_tags[i]
    #     for j in range(len(sentence)):
    #         word = sentence[j]
    #         predicted_tag = predicted_tags[j]
    #         f.write(word + " " + predicted_tag)
    #         f.write("\n")
    #     f.write("\n")
    # f.close()

    print("Testing Complete")


run()

