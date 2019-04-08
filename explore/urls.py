from django.conf.urls import url
from django.contrib import admin
from django.urls import path, re_path, include
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("pos_tagger", views.pos_tagger, name="pos_tagger"),
    path("ner", views.ner, name="ner"),
    path("gender_number", views.gender_number, name="gender_number"),
    path("np_extraction", views.np_extraction, name="np_extraction"),
    path(
        "coreference_resolution",
        views.coreference_resolution,
        name="coreference_resolution",
    ),
    path("test", views.test, name="test"),
    path("document/<int:id>", views.document, name="document"),
]
