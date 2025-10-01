# Generated migration
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_sitestats_pageview"),
    ]

    operations = [
        # Add featured artists field
        migrations.AddField(
            model_name="song",
            name="featured_artists",
            field=models.ManyToManyField(
                blank=True, related_name="featured_songs", to="core.artist"
            ),
        ),
        # Update artist field relationship name
        migrations.AlterField(
            model_name="song",
            name="artist",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="main_songs",
                to="core.artist",
            ),
        ),
        # Rename the old album field temporarily
        migrations.RenameField(
            model_name='song',
            old_name='album',
            new_name='album_old',
        ),
    ]
