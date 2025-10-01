# Generated migration
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_rename_album_add_featured_artists"),
    ]

    operations = [
        # Create the Album model
        migrations.CreateModel(
            name="Album",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(blank=True, unique=True)),
                ("year", models.IntegerField(blank=True, null=True)),
                (
                    "artist",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="albums",
                        to="core.artist",
                    ),
                ),
            ],
            options={
                "unique_together": {("title", "artist")},
            },
        ),
        # Add the new album field as ForeignKey
        migrations.AddField(
            model_name='song',
            name='album',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="songs",
                to="core.album",
            ),
        ),
    ]
