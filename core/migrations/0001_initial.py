# Generated by Django 5.1.3 on 2025-03-05 15:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('code', models.CharField(max_length=24, primary_key=True, serialize=False)),
                ('hash', models.CharField(max_length=24)),
                ('ctype', models.CharField(choices=[('xyz', 'Mock type, DNE'), ('url', 'URL'), ('txt', 'Text'), ('pic', 'Picture')], max_length=3)),
                ('btime', models.DateTimeField(auto_now_add=True)),
                ('mtime', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('name', models.CharField(max_length=32)),
                ('pass_hash', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='LinkItem',
            fields=[
                ('item', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='core.item')),
                ('url', models.URLField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='PicItem',
            fields=[
                ('item', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='core.item')),
                ('format', models.CharField(choices=[('jpg', 'JPEG'), ('gif', 'GIF'), ('png', 'PNG')], max_length=4)),
                ('size', models.IntegerField()),
            ],
        ),
    ]
