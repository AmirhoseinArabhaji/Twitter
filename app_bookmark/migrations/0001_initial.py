# Generated by Django 4.0.4 on 2022-05-19 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bookmark',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'bookmark',
                'verbose_name_plural': 'bookmarks',
                'ordering': ('-created_at',),
            },
        ),
    ]
