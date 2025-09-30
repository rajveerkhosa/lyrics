# lyricslib/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("core.urls")),   # <— all site routes live in core.urls
    path("admin/", admin.site.urls),
]
