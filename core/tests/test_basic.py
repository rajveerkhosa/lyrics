from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from core.models import Artist, Song, Line
import csv, tempfile

class ImportAndViewsTest(TestCase):
    def setUp(self):
        # build a small CSV in a temp file
        self.tmp = tempfile.NamedTemporaryFile(mode="w+", newline="", suffix=".csv", delete=False, encoding="utf-8")
        writer = csv.DictWriter(self.tmp, fieldnames=["no","original","romanized","translation_en"])
        writer.writeheader()
        writer.writerow({"no":"1","original":"ਕਿਸਮਤ","romanized":"","translation_en":"Fate"})
        writer.writerow({"no":"2","original":"ਮੇਹਨਤ","romanized":"mehnat","translation_en":"Hard work"})
        self.tmp.flush()

        # run your import command once for the suite
        call_command(
            "import_song",
            self.tmp.name,
            artist="Sidhu Moose Wala",
            title="295",
            year=2021,
            publish=True,
        )

    def test_home_lists_song(self):
        resp = self.client.get("/")
        self.assertContains(resp, "295")
        self.assertContains(resp, "Sidhu Moose Wala")

    def test_song_view_renders_lines(self):
        song = Song.objects.get(title="295")
        url = reverse("song_detail", kwargs={"artist": song.artist.slug, "song": song.slug})
        resp = self.client.get(url)
        self.assertContains(resp, "ਕਿਸਮਤ")
        self.assertContains(resp, "Hard work")

    def test_search_finds_line(self):
        resp = self.client.get("/search/?q=mehnat")
        self.assertContains(resp, "295")
        self.assertContains(resp, "mehnat")
