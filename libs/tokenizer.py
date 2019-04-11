import re


def tokenize(sentence):
    sentence = sentence.strip()
    sentence = sentence.replace("‘", "'")
    sentence = sentence.replace("’", "'")
    sentence = sentence.replace("“", '"')
    sentence = sentence.replace("”", '"')
    # sentence = re.sub(r"([^\w\s\d])", r" \1", sentence)

    sentence = sentence.replace("-LSB-", "")
    sentence = sentence.replace("-RSB-", "")

    sentence = re.sub(r"(\w)\.(\w)\.(\w)\.", r"\1\2\3", sentence)
    sentence = re.sub(r"(\w)\.(\w)\.", r"\1\2", sentence)
    sentence = re.sub(r"(\w+)n\'t", r"\1 not", sentence)
    sentence = re.sub(r"I'm", r"I am", sentence)
    sentence = re.sub(r"(\w+)\'ve", r"\1 have", sentence)
    sentence = re.sub(r"(\w+)\'re", r"\1 are", sentence)
    sentence = re.sub(r"(\w+)\'ll", r"\1 will", sentence)

    sentence = re.sub(r"([^\W])([^\w\d\s])", r"\1 \2", sentence)
    sentence = re.sub(r"([^\w\d\s])([^\W])", r"\1 \2", sentence)
    sentence = re.sub(r"(\w)\s-\s(\w)", r"\1-\2", sentence)

    sentence = re.sub(r"\'\ss", r"\'s", sentence)

    sentence = re.sub(r"(\d+)\s([\.\,])\s(\d+)", r"\1\2\3", sentence)
    sentence = re.sub(r"(\d+)\s([\.])", r"\1\2", sentence)
    sentence = re.sub(r"([\.])\s(\d+)", r"\1\2", sentence)

    sentence = re.sub(r"\'([^\'\"]+)\s+\'", r"' \1 '", sentence)
    sentence = re.sub(r"\"([^\'\"]+)\s+\"", r'" \1 "', sentence)

    while re.search(r"\(([^\(\)]+)\s+\)", sentence):
        sentence = re.sub(r"\(([^\(\)]+)\s+\)", r"\( \1 \)", sentence)

    return sentence.strip().split()
