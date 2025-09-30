# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Artist, Song, Line, UserProfile, SongComment, ArtistComment, SongRating, ArtistRating
from .forms import SignUpForm, LoginForm, SongCommentForm, ArtistCommentForm, SongRatingForm, ArtistRatingForm


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
    """A-Z list of all published songs."""
    songs = (
        Song.objects.filter(is_published=True)
        .select_related("artist")
        .order_by("title")
    )
    return render(request, "songs_index.html", {"songs": songs})


def artist_detail(request, artist):
    a = get_object_or_404(Artist, slug=artist)
    songs = (
        Song.objects.filter(artist=a, is_published=True)
        .select_related("artist")
        .order_by("-year", "title")
    )
    years = list(songs.exclude(year__isnull=True).values_list("year", flat=True))
    year_min, year_max = (min(years), max(years)) if years else (None, None)

    # Get comments and ratings
    comments = a.comments.select_related('user').all()
    avg_rating = a.ratings.aggregate(Avg('rating'))['rating__avg']
    user_rating = None
    is_favorite = False

    if request.user.is_authenticated:
        user_rating = a.ratings.filter(user=request.user).first()
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        is_favorite = profile.favorite_artists.filter(id=a.id).exists()

    # Handle comment submission
    if request.method == 'POST' and request.user.is_authenticated:
        if 'comment_text' in request.POST:
            comment_form = ArtistCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.artist = a
                comment.user = request.user
                comment.save()
                messages.success(request, 'Comment added!')
                return redirect('artist_detail', artist=artist)
        elif 'rating' in request.POST:
            rating_form = ArtistRatingForm(request.POST)
            if rating_form.is_valid():
                rating, created = ArtistRating.objects.update_or_create(
                    artist=a,
                    user=request.user,
                    defaults={'rating': rating_form.cleaned_data['rating']}
                )
                messages.success(request, 'Rating updated!' if not created else 'Rating added!')
                return redirect('artist_detail', artist=artist)

    comment_form = ArtistCommentForm()
    rating_form = ArtistRatingForm(instance=user_rating)

    return render(
        request,
        "artist_detail.html",
        {
            "artist": a,
            "songs": songs,
            "year_min": year_min,
            "year_max": year_max,
            "comments": comments,
            "comment_form": comment_form,
            "rating_form": rating_form,
            "avg_rating": avg_rating,
            "user_rating": user_rating,
            "is_favorite": is_favorite,
        },
    )


def song_detail(request, artist, song):
    import json
    s = get_object_or_404(
        Song.objects.select_related("artist").prefetch_related("lines"),
        artist__slug=artist,
        slug=song,
        is_published=True,
    )

    # Get comments and ratings
    comments = s.comments.select_related('user').all()
    avg_rating = s.ratings.aggregate(Avg('rating'))['rating__avg']
    user_rating = None
    is_favorite = False

    if request.user.is_authenticated:
        user_rating = s.ratings.filter(user=request.user).first()
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        is_favorite = profile.favorite_songs.filter(id=s.id).exists()

    # Handle comment submission
    if request.method == 'POST' and request.user.is_authenticated:
        if 'comment_text' in request.POST:
            comment_form = SongCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.song = s
                comment.user = request.user
                comment.save()
                messages.success(request, 'Comment added!')
                return redirect('song_detail', artist=artist, song=song)
        elif 'rating' in request.POST:
            rating_form = SongRatingForm(request.POST)
            if rating_form.is_valid():
                rating, created = SongRating.objects.update_or_create(
                    song=s,
                    user=request.user,
                    defaults={'rating': rating_form.cleaned_data['rating']}
                )
                messages.success(request, 'Rating updated!' if not created else 'Rating added!')
                return redirect('song_detail', artist=artist, song=song)

    comment_form = SongCommentForm()
    rating_form = SongRatingForm(instance=user_rating)

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
        "comments": comments,
        "comment_form": comment_form,
        "rating_form": rating_form,
        "avg_rating": avg_rating,
        "user_rating": user_rating,
        "is_favorite": is_favorite,
    })


# Authentication views
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('charts')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created.')
            return redirect('charts')
    else:
        form = SignUpForm()

    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('charts')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect(request.GET.get('next', 'charts'))
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('charts')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    favorite_songs = profile.favorite_songs.select_related('artist').all()
    favorite_artists = profile.favorite_artists.all()

    return render(request, 'profile.html', {
        'profile': profile,
        'favorite_songs': favorite_songs,
        'favorite_artists': favorite_artists,
    })


@login_required
def toggle_favorite_song(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.favorite_songs.filter(id=song_id).exists():
        profile.favorite_songs.remove(song)
        messages.info(request, f'{song.title} removed from favorites.')
    else:
        profile.favorite_songs.add(song)
        messages.success(request, f'{song.title} added to favorites!')

    return redirect(request.META.get('HTTP_REFERER', 'charts'))


@login_required
def toggle_favorite_artist(request, artist_id):
    artist = get_object_or_404(Artist, id=artist_id)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if profile.favorite_artists.filter(id=artist_id).exists():
        profile.favorite_artists.remove(artist)
        messages.info(request, f'{artist.name} removed from favorites.')
    else:
        profile.favorite_artists.add(artist)
        messages.success(request, f'{artist.name} added to favorites!')

    return redirect(request.META.get('HTTP_REFERER', 'charts'))
