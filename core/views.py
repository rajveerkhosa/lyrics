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
    album_matches = Album.objects.none()
    artist_matches = Artist.objects.none()

    if q:
        song_matches = (
            Song.objects.filter(is_published=True)
            .filter(Q(title__icontains=q) | Q(artist__name__icontains=q) | Q(album__title__icontains=q))
            .select_related("artist", "album")
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
        album_matches = (
            Album.objects.filter(Q(title__icontains=q) | Q(artist__name__icontains=q))
            .select_related("artist")
            .distinct()
        )
        artist_matches = Artist.objects.filter(Q(name__icontains=q)).distinct()

    sp = Paginator(song_matches, 20)
    lp = Paginator(line_matches, 20)
    ap = Paginator(album_matches, 20)
    arp = Paginator(artist_matches, 20)
    return render(
        request,
        "search.html",
        {
            "q": q,
            "songs_page": sp.get_page(request.GET.get("sp") or 1),
            "lines_page": lp.get_page(request.GET.get("lp") or 1),
            "albums_page": ap.get_page(request.GET.get("ap") or 1),
            "artists_page": arp.get_page(request.GET.get("arp") or 1),
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


def stats_view(request):
    """Private stats dashboard showing site analytics"""
    from django.contrib.auth.models import User
    from django.db.models import Count, Avg

    # Time periods
    now = timezone.now()
    today = now.date()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    # USER STATISTICS
    total_users = User.objects.count()
    active_users_7d = PageView.objects.filter(
        viewed_at__gte=seven_days_ago,
        user__isnull=False
    ).values('user').distinct().count()
    active_users_30d = PageView.objects.filter(
        viewed_at__gte=thirty_days_ago,
        user__isnull=False
    ).values('user').distinct().count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    new_users_7d = User.objects.filter(date_joined__gte=seven_days_ago).count()
    new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()

    # CONTENT STATISTICS
    total_songs = Song.objects.filter(is_published=True).count()
    total_unpublished_songs = Song.objects.filter(is_published=False).count()
    total_artists = Artist.objects.count()
    total_albums = Album.objects.count()
    total_song_comments = SongComment.objects.count()
    total_artist_comments = ArtistComment.objects.count()
    total_song_ratings = SongRating.objects.count()
    total_artist_ratings = ArtistRating.objects.count()
    total_lines = Line.objects.count()

    # TRAFFIC STATISTICS
    total_views = PageView.objects.count()
    views_today = PageView.objects.filter(viewed_at__date=today).count()
    views_7d = PageView.objects.filter(viewed_at__gte=seven_days_ago).count()
    views_30d = PageView.objects.filter(viewed_at__gte=thirty_days_ago).count()

    unique_ips_total = PageView.objects.values('ip_address').distinct().count()
    unique_ips_today = PageView.objects.filter(viewed_at__date=today).values('ip_address').distinct().count()
    unique_ips_7d = PageView.objects.filter(viewed_at__gte=seven_days_ago).values('ip_address').distinct().count()
    unique_ips_30d = PageView.objects.filter(viewed_at__gte=thirty_days_ago).values('ip_address').distinct().count()

    registered_views = PageView.objects.filter(user__isnull=False).count()
    anonymous_views = PageView.objects.filter(user__isnull=True).count()

    # TOP CONTENT
    # Get top URLs with view counts, then fetch actual objects to get titles
    top_song_urls = PageView.objects.filter(content_type='song').values(
        'url'
    ).annotate(
        views=Count('id')
    ).order_by('-views')[:10]

    top_songs = []
    for item in top_song_urls:
        url = item['url']
        # Parse URL: /a/<artist-slug>/<song-slug>/
        parts = url.strip('/').split('/')
        if len(parts) >= 3:
            try:
                song = Song.objects.select_related('artist').get(
                    artist__slug=parts[1],
                    slug=parts[2]
                )
                top_songs.append({
                    'url': url,
                    'content_title': f"{song.title} — {song.artist.name}",
                    'views': item['views']
                })
            except Song.DoesNotExist:
                pass

    top_artist_urls = PageView.objects.filter(content_type='artist').values(
        'url'
    ).annotate(
        views=Count('id')
    ).order_by('-views')[:10]

    top_artists = []
    for item in top_artist_urls:
        url = item['url']
        # Parse URL: /a/<artist-slug>/
        parts = url.strip('/').split('/')
        if len(parts) >= 2:
            try:
                artist = Artist.objects.get(slug=parts[1])
                top_artists.append({
                    'url': url,
                    'content_title': artist.name,
                    'views': item['views']
                })
            except Artist.DoesNotExist:
                pass

    top_album_urls = PageView.objects.filter(content_type='album').values(
        'url'
    ).annotate(
        views=Count('id')
    ).order_by('-views')[:10]

    top_albums = []
    for item in top_album_urls:
        url = item['url']
        # Parse URL: /album/<artist-slug>/<album-slug>/
        parts = url.strip('/').split('/')
        if len(parts) >= 3:
            try:
                album = Album.objects.select_related('artist').get(
                    artist__slug=parts[1],
                    slug=parts[2]
                )
                top_albums.append({
                    'url': url,
                    'content_title': f"{album.title} — {album.artist.name}",
                    'views': item['views']
                })
            except Album.DoesNotExist:
                pass

    # ENGAGEMENT STATISTICS
    total_song_favorites = UserProfile.objects.annotate(
        fav_count=Count('favorite_songs')
    ).aggregate(total=Count('favorite_songs'))['total'] or 0

    total_artist_favorites = UserProfile.objects.annotate(
        fav_count=Count('favorite_artists')
    ).aggregate(total=Count('favorite_artists'))['total'] or 0

    avg_song_rating = SongRating.objects.aggregate(avg=Avg('rating'))['avg']
    avg_artist_rating = ArtistRating.objects.aggregate(avg=Avg('rating'))['avg']

    # Calculate average comments/ratings per day
    if total_users > 0:
        days_since_launch = (now - User.objects.order_by('date_joined').first().date_joined).days or 1
        comments_per_day = (total_song_comments + total_artist_comments) / days_since_launch
        ratings_per_day = (total_song_ratings + total_artist_ratings) / days_since_launch
    else:
        comments_per_day = 0
        ratings_per_day = 0

    context = {
        # Users
        'total_users': total_users,
        'active_users_7d': active_users_7d,
        'active_users_30d': active_users_30d,
        'new_users_today': new_users_today,
        'new_users_7d': new_users_7d,
        'new_users_30d': new_users_30d,

        # Content
        'total_songs': total_songs,
        'total_unpublished_songs': total_unpublished_songs,
        'total_artists': total_artists,
        'total_albums': total_albums,
        'total_song_comments': total_song_comments,
        'total_artist_comments': total_artist_comments,
        'total_song_ratings': total_song_ratings,
        'total_artist_ratings': total_artist_ratings,
        'total_lines': total_lines,

        # Traffic
        'total_views': total_views,
        'views_today': views_today,
        'views_7d': views_7d,
        'views_30d': views_30d,
        'unique_ips_total': unique_ips_total,
        'unique_ips_today': unique_ips_today,
        'unique_ips_7d': unique_ips_7d,
        'unique_ips_30d': unique_ips_30d,
        'registered_views': registered_views,
        'anonymous_views': anonymous_views,

        # Top Content
        'top_songs': top_songs,
        'top_artists': top_artists,
        'top_albums': top_albums,

        # Engagement
        'total_song_favorites': total_song_favorites,
        'total_artist_favorites': total_artist_favorites,
        'avg_song_rating': avg_song_rating,
        'avg_artist_rating': avg_artist_rating,
        'comments_per_day': comments_per_day,
        'ratings_per_day': ratings_per_day,
    }

    return render(request, 'stats.html', context)
