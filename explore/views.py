from django.http import HttpRequest
from django.shortcuts import render, redirect
from libs.pos_tagger import pos_tag
from libs.ner import named_entities
from libs.tokenizer import tokenize
from libs.gender_number import get_gender_number
from libs.utils2 import extract_noun_phrases, extract_tagged_entities
from libs.coreference_resolver import *
from libs.document import view
import nltk


def home(request):
    return render(request, "home.html")


def pos_tagger(request):
    title = "Parts of Speech Tagging"
    if request.method == "POST":
        text = request.POST["text"]
        tokenized_sentence = tokenize(text)
        tagged_sentence = pos_tag(tokenized_sentence)
        result = list(zip(tokenized_sentence, tagged_sentence))
        return render(
            request, "pos_tagger.html", {"title": title, "result": result, "text": text}
        )
    else:
        return render(request, "pos_tagger.html", {"title": title})


def ner(request):
    title = "Named Entity Recognition"
    if request.method == "POST":
        text = request.POST["text"]
        tokenized_sentence = tokenize(text)
        tagged_sentence = named_entities(tokenized_sentence)
        tagged_entities = extract_tagged_entities(
            list(zip(tokenized_sentence, tagged_sentence))
        )
        result = []
        for entity, tag in tagged_entities:
            result.append(entity + " - " + tag)
        return render(
            request, "ner.html", {"title": title, "result": result, "text": text}
        )
    else:
        return render(request, "ner.html", {"title": title})


def gender_number(request):
    title = "Gender and Number Identification"
    if request.method == "POST":
        text = request.POST["text"]
        result = " ".join(get_gender_number(text, full=True))
        return render(
            request,
            "gender_number.html",
            {"title": title, "result": result, "text": text},
        )
    else:
        return render(request, "gender_number.html", {"title": title})


def np_extraction(request):
    title = "Noun Phrase Extraction"
    if request.method == "POST":
        text = request.POST["text"]
        result = []
        for txt in nltk.sent_tokenize(text):
            result += extract_noun_phrases(txt)
        return render(
            request,
            "np_extraction.html",
            {"title": title, "result": result, "text": text},
        )
    else:
        return render(request, "np_extraction.html", {"title": title})


def coreference_resolution(request):
    title = "Coreference Resolution"
    if request.method == "POST":
        text = request.POST["text"]
        result = ""
        cr = CoreferenceResolution(text)
        result = cr.resolve()

        return render(
            request,
            "coreference_resolution.html",
            {"title": title, "result": result, "text": text},
        )
    else:
        return render(request, "coreference_resolution.html", {"title": title})


def test(request):
    cr = CoreferenceResolution()
    result = cr.test()
    return render(request, "test.html", {"result": result})


def document(request, id):
    return render(request, "document.html", {"document": view(id)})
