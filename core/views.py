# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from .models import Artist, Album, Song, Line, UserProfile, SongComment, ArtistComment, SongRating, ArtistRating, PageView
from .forms import SignUpForm, LoginForm, SongCommentForm, ArtistCommentForm, SongRatingForm, ArtistRatingForm


def charts(request):
    """Homepage: Top charts / featured based on weekly views."""
    # Get views from the last 7 days
    seven_days_ago = timezone.now() - timedelta(days=7)

    # Get top songs by weekly views
    weekly_song_views = (
        PageView.objects.filter(
            content_type='song',
            viewed_at__gte=seven_days_ago
        )
        .values('url')
        .annotate(view_count=Count('id'))
        .order_by('-view_count')[:10]
    )

    # Extract song slugs from URLs and get Song objects
    top_songs = []
    for view_data in weekly_song_views:
        url = view_data['url']
        # URL format: /a/<artist-slug>/<song-slug>/
        parts = url.strip('/').split('/')
        if len(parts) >= 3 and parts[0] == 'a':
            artist_slug = parts[1]
            song_slug = parts[2]
            try:
                song = Song.objects.select_related('artist', 'album').get(
                    artist__slug=artist_slug,
                    slug=song_slug,
                    is_published=True
                )
                song.weekly_views = view_data['view_count']
                top_songs.append(song)
            except Song.DoesNotExist:
                pass

    # Get top artists by weekly views
    weekly_artist_views = (
        PageView.objects.filter(
            content_type='artist',
            viewed_at__gte=seven_days_ago
        )
        .values('url')
        .annotate(view_count=Count('id'))
        .order_by('-view_count')[:6]
    )

    # Extract artist slugs from URLs and get Artist objects
    featured_artists = []
    for view_data in weekly_artist_views:
        url = view_data['url']
        # URL format: /a/<artist-slug>/
        parts = url.strip('/').split('/')
        if len(parts) >= 2 and parts[0] == 'a':
            artist_slug = parts[1]
            try:
                artist = Artist.objects.get(slug=artist_slug)
                artist.weekly_views = view_data['view_count']
                featured_artists.append(artist)
            except Artist.DoesNotExist:
                pass

    # Fallback: if no views yet, show recent songs and all artists
    if not top_songs:
        top_songs = list(
            Song.objects.filter(is_published=True)
            .select_related("artist", "album")
            .order_by("-year", "title")[:10]
        )
        for song in top_songs:
            song.weekly_views = 0

    if not featured_artists:
        featured_artists = list(Artist.objects.order_by("name")[:6])
        for artist in featured_artists:
            artist.weekly_views = 0

    songs = (
        Song.objects.filter(is_published=True)
        .select_related("artist", "album")
        .order_by("artist__name", "title")
    )
    artists = Artist.objects.order_by("name")

    return render(
        request,
        "charts.html",
        {
            "artists": artists,
            "songs": songs,
            "top_songs": top_songs,
            "featured_artists": featured_artists,
        },
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
    """A–Z list of albums."""
    albums = Album.objects.select_related('artist').order_by('title')
    return render(request, "albums_index.html", {"albums": albums})


def songs_index(request):
    """A-Z list of all published songs."""
    songs = (
        Song.objects.filter(is_published=True)
        .select_related("artist", "album")
        .order_by("title")
    )
    return render(request, "songs_index.html", {"songs": songs})


def artist_detail(request, artist):
    a = get_object_or_404(Artist, slug=artist)
    # Get songs where this artist is the main artist
    main_songs = (
        Song.objects.filter(artist=a, is_published=True)
        .select_related("artist")
        .order_by("-year", "title")
    )
    # Get songs where this artist is featured
    featured_songs = (
        Song.objects.filter(featured_artists=a, is_published=True)
        .select_related("artist")
        .order_by("-year", "title")
    )
    # Combine both querysets
    from itertools import chain
    songs = list(chain(main_songs, featured_songs))
    # Sort by year and title
    songs = sorted(songs, key=lambda s: (-(s.year or 0), s.title))

    years = [s.year for s in songs if s.year]
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

    # Get view count for this artist
    artist_views = PageView.objects.filter(content_type='artist', url=request.path).count()

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
            "view_count": artist_views,
        },
    )


def album_detail(request, artist, album):
    """Album detail page showing all songs in the album."""
    a = get_object_or_404(Artist, slug=artist)
    alb = get_object_or_404(Album, slug=album, artist=a)

    # Get all songs in this album
    songs = Song.objects.filter(album=alb, is_published=True).select_related('artist').order_by('title')

    # Get view count for this album
    album_views = PageView.objects.filter(content_type='album', url=request.path).count()

    return render(request, 'album_detail.html', {
        'album': alb,
        'artist': a,
        'songs': songs,
        'view_count': album_views,
    })


def song_detail(request, artist, song):
    import json
    s = get_object_or_404(
        Song.objects.select_related("artist", "album").prefetch_related("lines", "featured_artists"),
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

    # Get view count for this song
    song_views = PageView.objects.filter(content_type='song', url=request.path).count()

    return render(request, "song_detail.html", {
        "song": s,
        "lyrics_json": json.dumps(lyrics_data),
        "comments": comments,
        "comment_form": comment_form,
        "rating_form": rating_form,
        "avg_rating": avg_rating,
        "user_rating": user_rating,
        "is_favorite": is_favorite,
        "view_count": song_views,
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
