import json
import re


def dict_increase(d, k, v):
    temp_dict = d
    if k in temp_dict:
        temp_dict[k] += v
    else:
        temp_dict[k] = v
    return temp_dict

   



def read_train_file():
    with open("data/train.english.v4_gold_conll", "r", encoding="utf8") as f:
        dataset = f.read()
    f.close()
    words = []
    tags = []
    tag_count = {}
    word_count = {}
    lw = []
    lt = []
    for annotations in dataset.split("\n\n"):
        tag_count = dict_increase(tag_count, "<start>", 1)
        word_count = dict_increase(word_count, "<start>", 1)
        for line in annotations.split("\n"):
            line = re.sub(r"\s+", r"\t", line)
            line = line.split("\t")
            if len(line)<=4:
                continue
            w = line[3]
            t = line[4]
            print(line)
            print(w,t )
            lw.append(w.lower())
            lt.append(t)
            tag_count = dict_increase(tag_count, t, 1)
            word_count = dict_increase(word_count, w.lower(), 1)
        tag_count = dict_increase(tag_count, "<end>", 1)
        word_count = dict_increase(word_count, "<end>", 1)
        words.append(lw)
        tags.append(lt)
        lw = []
        lt = []
    return (words, tags, tag_count, word_count)


def train(train_list_words, train_list_tags, tag_count, word_count):

    transition_probability = {}

    emission_probability = {}

    singleton_transitions = {}

    singleton_emissions = {}

    # total umber of words
    n = 0

    for tags in train_list_tags:
        prev_tag = "<start>"
        n += len(tags)
        for tag in tags:
            if tag in transition_probability:
                transition_probability[tag] = dict_increase(
                    transition_probability[tag], prev_tag, 1
                )
            else:
                transition_probability[tag] = {}
                transition_probability[tag][prev_tag] = 1
            prev_tag = tag

        if "<end>" in transition_probability:
            transition_probability["<end>"] = dict_increase(
                transition_probability["<end>"], prev_tag, 1
            )
        else:
            transition_probability["<end>"] = {}
            transition_probability["<end>"][prev_tag] = 1

    for sentence in zip(train_list_words, train_list_tags):
        for (word, tag) in zip(sentence[0], sentence[1]):
            if word in emission_probability:
                emission_probability[word] = dict_increase(
                    emission_probability[word], tag, 1
                )
            else:
                emission_probability[word] = {}
                emission_probability[word][tag] = 1

    # number of words excluding <start> and <end>
    V = len(word_count) - 2

    # find singleton_probabilities#
    for word in emission_probability:
        for tag in emission_probability[word]:
            if emission_probability[word][tag] == 1:
                dict_increase(singleton_emissions, tag, 1)

    for tag2 in transition_probability:
        for tag1 in transition_probability[tag2]:
            if transition_probability[tag2][tag1] == 1:
                dict_increase(singleton_transitions, tag1, 1)

    # end singleton_probabilities#

    for tag2 in transition_probability:
        for tag1 in transition_probability[tag2]:
            k = (
                (1 + singleton_transitions[tag1])
                if tag1 in singleton_transitions
                else 1
            )
            transition_probability[tag2][tag1] = (
                transition_probability[tag2][tag1] + k * tag_count[tag2] / n
            ) / (tag_count[tag1] + k)

    for word in emission_probability:
        for tag in emission_probability[word]:
            k = (1 + singleton_emissions[tag]) if tag in singleton_emissions else 1
            emission_probability[word][tag] = (
                emission_probability[word][tag] + k * (word_count[word] + 1) / (n + V)
            ) / (tag_count[tag] + k)

    # for unknown words:

    total_tags_count = sum([x for x in tag_count.values()])
    emission_probability["<unknown>"] = {}
    for tag in tag_count:
        if tag != "<start>" and tag != "<end>":
            k = (1 + singleton_emissions[tag]) if tag in singleton_emissions else 1
            emission_probability["<unknown>"][tag] = k / (n + V) / (tag_count[tag] + k)

    # end unknown words

    # for unknown transitions

    for tag1 in tag_count:
        k = (1 + singleton_transitions[tag1]) if tag1 in singleton_transitions else 1
        for tag2 in tag_count:
            if (
                tag2 != "<start>"
                and tag1 != "<end>"
                and tag1 not in transition_probability[tag2]
            ):
                transition_probability[tag2][tag1] = (
                    k * (tag_count[tag2] / n) / (tag_count[tag1] + k)
                )

    # end unknown transitions

    return (transition_probability, emission_probability)


def run():
    words_list_train, tags_list_train, tag_count, word_count = read_train_file()
    transition_probability, emission_probability = train(
        words_list_train, tags_list_train, tag_count, word_count
    )

    probability = {}
    probability["emission"] = emission_probability
    probability["transition"] = transition_probability

    with open("data/pos_tagger_probability.json", "w") as f:
        json.dump(probability, f, indent=4)
    f.close()

    print("Training Complete")


run()

