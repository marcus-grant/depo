# Generated by Django 5.1.3 on 2024-11-15 21:05

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Shortcode',
            fields=[
                ('id', models.CharField(max_length=24, primary_key=True, serialize=False)),
                ('ctype', models.CharField(choices=[('url', 'URL'), ('txt', 'Text'), ('pic', 'Picture')], max_length=3)),
                ('url', models.URLField(blank=True, max_length=192, null=True)),
                ('btime', models.DateTimeField(auto_now_add=True)),
                ('mtime', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
