from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Artist, Song, Line


def home(request):
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
        "home.html",
        {"artists": artists, "songs": songs, "top_songs": top_songs, "featured_videos": featured_videos},
    )


def song_detail(request, artist, song):
    s = get_object_or_404(
        Song.objects.select_related("artist").prefetch_related("lines"),
        artist__slug=artist,
        slug=song,
        is_published=True,
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


def artist_detail(request, artist):
    """Artist profile page — no Top Charts here, only this artist info + songs."""
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
