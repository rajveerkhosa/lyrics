from django.core.management.base import BaseCommand
from django.db import transaction
import csv
from core.models import Artist, Song, Line

class Command(BaseCommand):
    help = "Import one song (lines) from a CSV."

    def add_arguments(self, parser):
        parser.add_argument("csv_path")
        parser.add_argument("--artist", required=True)
        parser.add_argument("--title", required=True)
        parser.add_argument("--year", type=int, default=None)
        parser.add_argument("--publish", action="store_true")

    @transaction.atomic
    def handle(self, csv_path, artist, title, year, publish, **_):
        # 1) Ensure artist/song exist; reuse if already there
        artist_obj, _ = Artist.objects.get_or_create(name=artist)
        song, created = Song.objects.get_or_create(
            artist=artist_obj,
            title=title,
            defaults={"year": year, "is_published": publish},
        )
        if not created:
            # idempotent re-import: wipe lines + update metadata
            Line.objects.filter(song=song).delete()
            song.year = year
            song.is_published = publish
            song.save()

        # 2) Read the CSV and create lines
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"no", "original", "translation_en"}
            if not required.issubset(reader.fieldnames or []):
                raise SystemExit(f"CSV must include headers: {sorted(required)}")

            for row in reader:
                Line.objects.create(
                    song=song,
                    no=int(row["no"]),
                    original=(row["original"] or "").strip(),
                    translation_en=(row["translation_en"] or "").strip(),
                    romanized=((row.get("romanized") or "").strip() or None),
                )

        self.stdout.write(self.style.SUCCESS(f"Imported {song.title}"))
