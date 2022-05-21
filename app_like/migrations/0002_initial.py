# Generated by Django 4.0.4 on 2022-05-19 07:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app_twitter', '0001_initial'),
        ('app_like', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='like',
            name='tweet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_twitter.tweet'),
        ),
        migrations.AddField(
            model_name='like',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='like',
            index=models.Index(fields=['-created_at'], name='app_like_li_created_4ee79c_idx'),
        ),
        migrations.AddIndex(
            model_name='like',
            index=models.Index(fields=['user', 'tweet', 'is_dislike'], name='app_like_li_user_id_934e2a_idx'),
        ),
        migrations.AddConstraint(
            model_name='like',
            constraint=models.UniqueConstraint(fields=('user', 'tweet', 'is_dislike'), name='like_unique_constraint'),
        ),
    ]
