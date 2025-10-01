# Generated migration
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_migrate_album_data"),
    ]

    operations = [
        # Remove the old album field
        migrations.RemoveField(
            model_name='song',
            name='album_old',
        ),
    ]
