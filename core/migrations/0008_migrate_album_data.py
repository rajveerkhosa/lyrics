# Data migration to convert old album CharField to Album objects
from django.db import migrations
from django.utils.text import slugify


def migrate_album_data(apps, schema_editor):
    Song = apps.get_model('core', 'Song')
    Album = apps.get_model('core', 'Album')

    # Get all songs with album_old values
    songs_with_albums = Song.objects.exclude(album_old__isnull=True).exclude(album_old='')

    for song in songs_with_albums:
        # Create or get the Album object
        album, created = Album.objects.get_or_create(
            title=song.album_old,
            artist=song.artist,
            defaults={
                'year': song.year,
                'slug': slugify(f"{song.artist.name}-{song.album_old}")
            }
        )

        # Set the new album ForeignKey
        song.album = album
        song.save()


def reverse_migrate_album_data(apps, schema_editor):
    Song = apps.get_model('core', 'Song')

    # Move data back from album to album_old
    songs_with_albums = Song.objects.exclude(album__isnull=True)

    for song in songs_with_albums:
        song.album_old = song.album.title
        song.save()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_create_album_model"),
    ]

    operations = [
        migrations.RunPython(migrate_album_data, reverse_migrate_album_data),
    ]
