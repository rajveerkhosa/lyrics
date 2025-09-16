from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Artist, Song, Line

def home(request):
    artists = Artist.objects.order_by("name").all()
    songs = Song.objects.filter(is_published=True).select_related("artist").order_by("artist__name", "title")
    return render(request, "home.html", {"artists": artists, "songs": songs})

def song_detail(request, artist, song):
    s = get_object_or_404(
        Song.objects.select_related("artist").prefetch_related("lines"),
        artist__slug=artist, slug=song, is_published=True
    )
    return render(request, "song_detail.html", {"song": s})

def search(request):
    q = (request.GET.get("q") or "").strip()
    song_matches = Song.objects.none()
    line_matches = Line.objects.none()

    if q:
        song_matches = (
            Song.objects.filter(is_published=True)
            .filter(Q(title__icontains=q) | Q(artist__name__icontains=q))
            .select_related("artist").distinct()
        )
        line_matches = (
            Line.objects.filter(
                Q(original__icontains=q) | Q(translation_en__icontains=q) | Q(romanized__icontains=q),
                song__is_published=True,
            )
            .select_related("song", "song__artist")
            .order_by("song__artist__name", "song__title", "no")
        )

    sp = Paginator(song_matches, 20)
    lp = Paginator(line_matches, 20)
    songs_page = sp.get_page(request.GET.get("sp") or 1)
    lines_page = lp.get_page(request.GET.get("lp") or 1)
    return render(request, "search.html", {"q": q, "songs_page": songs_page, "lines_page": lines_page})
