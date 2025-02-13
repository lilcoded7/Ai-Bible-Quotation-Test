# Generated by Django 5.1.6 on 2025-02-13 11:40

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BibleTranslation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('translation', models.CharField(max_length=10)),
                ('book_id', models.IntegerField()),
                ('book', models.CharField(max_length=50)),
                ('chapter', models.IntegerField()),
                ('verse', models.IntegerField()),
                ('text', models.TextField()),
            ],
            options={
                'unique_together': {('translation', 'book_id', 'chapter', 'verse')},
            },
        ),
    ]
