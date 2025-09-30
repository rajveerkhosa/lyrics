# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse

from .models import Artist, Song, Line


def charts(request):
    """Homepage: Top charts / featured."""
    top_songs = (
        Song.objects.filter(is_published=True)
        .select_related("artist")
        .order_by("-year", "title")[:5]
    )

    featured_videos = [
        {
            "title": "Shake It Off",
            "artist": "Taylor Swift",
            "thumbnail": "https://images.unsplash.com/photo-1694878982098-1cec80d96eca?auto=format&fit=crop&w=1200&q=60",
        },
        {
            "title": "Blinding Lights",
            "artist": "The Weeknd",
            "thumbnail": "https://images.unsplash.com/photo-1615821430614-3d7d2685e2f2?auto=format&fit=crop&w=1200&q=60",
        },
    ]

    songs = (
        Song.objects.filter(is_published=True)
        .select_related("artist")
        .order_by("artist__name", "title")
    )
    artists = Artist.objects.order_by("name")

    return render(
        request,
        "charts.html",   # you already have this template
        {"artists": artists, "songs": songs, "top_songs": top_songs, "featured_videos": featured_videos},
    )


def search(request):
    q = (request.GET.get("q") or "").strip()
    song_matches = Song.objects.none()
    line_matches = Line.objects.none()

    if q:
        song_matches = (
            Song.objects.filter(is_published=True)
            .filter(Q(title__icontains=q) | Q(artist__name__icontains=q))
            .select_related("artist")
            .distinct()
        )
        line_matches = (
            Line.objects.filter(
                Q(original__icontains=q)
                | Q(translation_en__icontains=q)
                | Q(romanized__icontains=q),
                song__is_published=True,
            )
            .select_related("song", "song__artist")
            .order_by("song__artist__name", "song__title", "no")
        )

    sp = Paginator(song_matches, 20)
    lp = Paginator(line_matches, 20)
    return render(
        request,
        "search.html",
        {
            "q": q,
            "songs_page": sp.get_page(request.GET.get("sp") or 1),
            "lines_page": lp.get_page(request.GET.get("lp") or 1),
        },
    )


def artists_index(request):
    """A–Z list of all artists."""
    artists = Artist.objects.order_by("name")
    return render(request, "artists_index.html", {"artists": artists})


def albums_index(request):
    """A–Z list of album names derived from songs."""
    # Adjust the field if your model uses a different album field name
    album_qs = (
        Song.objects.filter(is_published=True)
        .exclude(album__isnull=True)
        .exclude(album__exact="")
        .values_list("album", flat=True)
        .distinct()
    )
    albums = sorted(album_qs, key=lambda s: s.lower())
    return render(request, "albums_index.html", {"albums": albums})


def songs_index(request):
    """Per your spec: clicking 'Songs' shows artists A–Z as well."""
    return redirect(reverse("artists_index"))


def artist_detail(request, artist):
    a = get_object_or_404(Artist, slug=artist)
    songs = (
        Song.objects.filter(artist=a, is_published=True)
        .select_related("artist")
        .order_by("-year", "title")
    )
    years = list(songs.exclude(year__isnull=True).values_list("year", flat=True))
    year_min, year_max = (min(years), max(years)) if years else (None, None)

    return render(
        request,
        "artist_detail.html",
        {"artist": a, "songs": songs, "year_min": year_min, "year_max": year_max},
    )


def song_detail(request, artist, song):
    import json
    s = get_object_or_404(
        Song.objects.select_related("artist").prefetch_related("lines"),
        artist__slug=artist,
        slug=song,
        is_published=True,
    )
    # Prepare lyrics data for JavaScript
    lyrics_data = [
        {
            "no": line.no,
            "original": line.original,
            "romanized": line.romanized or "",
            "translation": line.translation_en,
        }
        for line in s.lines.all()
    ]
    return render(request, "song_detail.html", {
        "song": s,
        "lyrics_json": json.dumps(lyrics_data),
    })
