import json
import pandas as pd
import sys
import os

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

with open(os.path.join(__location__, "data/gender.csv"), "r") as src:
    dataset = dict((line.split("\t") for line in src if len(line.split("\t")) > 1))

full_form ={
    "M" : "Male",
    "F" : "Female",
    "N": "Neutral",
    "U": "Unknown",
    "S": "Singular",
    "P": "Plural"
}

def get_gender_number(a=None, pronoun=False, full=False):
    if not a:
        a = input()

    a = a.lower()


    gender = "U"
    number = "S"

    # df = pd.read_csv("data/gender.csv", delimiter="\t")

    # if a not in df.index:
    #     return (gender, number)

    # features = df.iloc[df.index.searchsorted(a)].features
    
    if pronoun==True or a not in dataset:
        with open(os.path.join(__location__, "data/pronouns.csv"), "r") as src:
            pronoun_gender_data = dict((line.strip().split("\t") for line in src if len(line.split("\t")) > 1))
        
        if a not in pronoun_gender_data:
            if full:
                return (full_form[gender], full_form[number])
            
            return (gender, number)

        gender,number = pronoun_gender_data[a].split(" ")

        if full:
            return (full_form[gender], full_form[number])

        return (gender, number)


    features = dataset[a]

    [male_occurences, female_occurences, neutral_occurences, plural_occurences] = [
        int(x) for x in features.split()
    ]

    total_occurences = male_occurences + female_occurences + neutral_occurences

    if total_occurences > 0:
        if male_occurences / total_occurences > 0.5:
            gender = "M"

        if female_occurences / total_occurences > 0.5:
            gender = "F"

        if neutral_occurences / total_occurences > 0.5:
            gender = "N"

        if plural_occurences / total_occurences > 0.5:
            number = "P"

    if full:
        return (full_form[gender], full_form[number])

    return (gender, number)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(get_gender_number(sys.argv[1]))
    else:
        print(get_gender_number())
