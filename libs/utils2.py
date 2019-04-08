import re
import os
from . import tokenizer, pos_tagger, gender_number


def extract_noun_phrases(sentence):
    tokenized_sentence = tokenizer.tokenize(sentence)
    tagged_sentence = pos_tagger.pos_tag(tokenized_sentence)
    state = -1
    cur = []
    noun_phrases = []
    start = -1
    prepositions = ["of", "for"]
    for word, tag in zip(tokenized_sentence, tagged_sentence):
        if state == -1 and tag == "PDT":
            state = 0
            cur.append((word, tag))
        elif (
            (state <= 0 or state == 3)
            and (tag[:2] == "DT")
            or (state == 2 and cur[-1][1] == "CC")
        ):
            state = 1
            cur.append((word, tag))
        elif (state <= 1 or state == 3) and (
            tag[:2] == "JJ" or tag == "CD" or tag == "PRP$"
        ):
            if state <= 0:
                state = 1
            cur.append((word, tag))
        elif state <= 4 and (
            tag[:2] == "NN"
            or tag == "SYM"
            or (state == 2 and tag == "CC")
            or (state == 2 and tag == "POS")
        ):
            state = 2
            cur.append((word, tag))
        elif state == 2 and word in prepositions:
            state = 3
            cur.append((word, tag))
        else:
            if state == 3:
                cur = cur[:-1]

            if state == 2 or state == 4 and len(cur):
                noun_phrases.append(" ".join([word for word, tag in cur]))

            cur = []
            state = -1

    if state == 2 or state == 4 and tag[:2] == "NN":
        if len(cur):
            noun_phrases.append(" ".join([word for word, tag in cur]))

    return noun_phrases


def extract_pronouns(sentence):
    tokenized_sentence = tokenizer.tokenize(sentence)
    tagged_sentence = pos_tagger.pos_tag(sentence)
    pronouns = []
    for word, tag in zip(tokenized_sentence, tagged_sentence):
        if tag[:3] == "PRP":
            pronouns.append(word)

    return pronouns


def extract_tagged_entities(tagged):
    entities = []
    cur = ""
    ner_tag = ""
    for word, tag in tagged:
        cur_tag = tag.split("-")
        if len(cur_tag) == 2:
            if cur_tag[0] == "B":
                if len(cur) and len(ner_tag):
                    entities.append((cur, ner_tag))
                cur = word
                ner_tag = cur_tag[1]
            else:
                cur += " " + word
    if len(cur) and len(ner_tag):
        entities.append((cur, ner_tag))
    return entities

