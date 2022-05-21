# Generated by Django 4.0.4 on 2022-05-19 07:54

from django.conf import settings
import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app_vote', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BlockList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('-updated_at',),
            },
        ),
        migrations.CreateModel(
            name='Fellowship',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('created_at',),
            },
        ),
        migrations.CreateModel(
            name='Hashtag',
            fields=[
                ('name', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('usage_count', models.PositiveBigIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('-usage_count',),
            },
        ),
        migrations.CreateModel(
            name='HashtagsUsedInTweets',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hashtag', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app_twitter.hashtag')),
            ],
        ),
        migrations.CreateModel(
            name='Mention',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mention_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mention_by_user', to=settings.AUTH_USER_MODEL)),
                ('mention_to', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mention_to_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MentionUsedInTweets',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mention', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app_twitter.mention')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('body', models.TextField(editable=False)),
                ('seen', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('contact', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='WaitingForResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('following', 'following'), ('direct message', 'direct message')], default='following', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('from_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('to_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='Tweet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.CharField(max_length=5000, null=True)),
                ('images', models.JSONField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('likes_count', models.PositiveIntegerField(default=0)),
                ('views_count', models.PositiveBigIntegerField(default=0)),
                ('mentions_count', models.PositiveIntegerField(default=0)),
                ('retweets_count', models.PositiveIntegerField(default=0)),
                ('related_item_object_id', models.PositiveIntegerField(null=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('hashtags', models.ManyToManyField(through='app_twitter.HashtagsUsedInTweets', to='app_twitter.hashtag')),
                ('mentions', models.ManyToManyField(through='app_twitter.MentionUsedInTweets', to='app_twitter.mention')),
                ('related_item_content_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content_type_tweets', to='contenttypes.contenttype')),
                ('reply_to', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='app_twitter.tweet')),
                ('retweet', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='retweets', to='app_twitter.tweet')),
                ('vote', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app_vote.vote')),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='MutedUsers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('muted', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('muter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='MessagesInConversation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_twitter.conversation')),
                ('message', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app_twitter.message')),
            ],
        ),
        migrations.AddField(
            model_name='mentionusedintweets',
            name='tweet',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app_twitter.tweet'),
        ),
        migrations.AddField(
            model_name='hashtagsusedintweets',
            name='tweet',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app_twitter.tweet'),
        ),
        migrations.AddIndex(
            model_name='hashtag',
            index=models.Index(fields=['-usage_count'], name='app_twitter_usage_c_cad5af_idx'),
        ),
        migrations.AddIndex(
            model_name='hashtag',
            index=django.contrib.postgres.indexes.HashIndex(fields=['name'], name='hashtag_name_hash_index'),
        ),
        migrations.AddField(
            model_name='fellowship',
            name='follower',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='fellowship',
            name='following',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followed', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='conversation',
            name='contact_participant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='conversation',
            name='messages',
            field=models.ManyToManyField(through='app_twitter.MessagesInConversation', to='app_twitter.message'),
        ),
        migrations.AddField(
            model_name='conversation',
            name='starter_participant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='blocklist',
            name='blocked',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='blocklist',
            name='blocker',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='waitingforresponse',
            index=models.Index(fields=['from_user', 'to_user', 'type'], name='app_twitter_from_us_5b1f6f_idx'),
        ),
        migrations.AddConstraint(
            model_name='waitingforresponse',
            constraint=models.UniqueConstraint(fields=('from_user', 'to_user', 'type'), name='from_to_type_waiting_constraint'),
        ),
        migrations.AddIndex(
            model_name='tweet',
            index=models.Index(fields=['-created_at'], name='tweet_created_at_tree_index'),
        ),
        migrations.AddIndex(
            model_name='tweet',
            index=models.Index(fields=['related_item_content_type', 'related_item_object_id'], name='related_item_tree_index'),
        ),
        migrations.AddIndex(
            model_name='tweet',
            index=django.contrib.postgres.indexes.HashIndex(fields=['author'], name='tweet_author_hash_index'),
        ),
        migrations.AddIndex(
            model_name='tweet',
            index=django.contrib.postgres.indexes.HashIndex(fields=['retweet'], name='tweet_retweet_hash_index'),
        ),
        migrations.AddIndex(
            model_name='tweet',
            index=django.contrib.postgres.indexes.HashIndex(fields=['reply_to'], name='tweet_reply_to_hash_index'),
        ),
        migrations.AddIndex(
            model_name='mutedusers',
            index=models.Index(fields=['muter', 'muted'], name='app_twitter_muter_i_59f617_idx'),
        ),
        migrations.AddIndex(
            model_name='messagesinconversation',
            index=models.Index(fields=['-created_at', 'message'], name='app_twitter_created_c874f1_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=django.contrib.postgres.indexes.HashIndex(fields=['id'], name='app_twitter_id_a4b629_hash'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['id', 'contact'], name='app_twitter_id_c7b784_idx'),
        ),
        migrations.AddIndex(
            model_name='fellowship',
            index=models.Index(fields=['follower', 'following'], name='app_twitter_followe_424735_idx'),
        ),
        migrations.AddIndex(
            model_name='fellowship',
            index=models.Index(fields=['-created_at'], name='fellowship_created_index'),
        ),
        migrations.AddConstraint(
            model_name='fellowship',
            constraint=models.UniqueConstraint(fields=('follower', 'following'), name='fellowship_unique'),
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['starter_participant', 'contact_participant'], name='conversation_participant_index'),
        ),
        migrations.AddIndex(
            model_name='blocklist',
            index=models.Index(fields=['blocker', 'blocked'], name='app_twitter_blocker_e79c64_idx'),
        ),
        migrations.AddConstraint(
            model_name='blocklist',
            constraint=models.UniqueConstraint(fields=('blocker', 'blocked'), name='block_unique_constraints'),
        ),
    ]
