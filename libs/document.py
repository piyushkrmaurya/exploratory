import sys
import os
import re

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def view(id):
    with open(
        os.path.join(__location__, "data/train.english.v4_gold_conll"),
        "r",
        encoding="utf8",
    ) as f:
        dataset = f.read().split("\n\n#end document")
    f.close()

    sentences = ""
    if id <= len(dataset):

        annotations = dataset[id]
        words = []

        for annotation in annotations.split("\n"):
            annotation = re.sub(r"\s+", r"\t", annotation)
            annotation = annotation.split("\t")
            if len(annotation) <= 10:
                continue

            word = annotation[3]
            words.append(word)

        sentences = " ".join(words)

    return sentences
