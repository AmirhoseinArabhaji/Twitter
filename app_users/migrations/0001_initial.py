# Generated by Django 4.0.4 on 2022-05-16 10:06

import app_users.models
import django.contrib.postgres.indexes
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('type', models.CharField(choices=[('NORMAL', 'normal user'), ('STAFF', 'staff user'), ('SUPERUSER', 'super user')], db_index=True, default='NORMAL', max_length=64)),
                ('is_active', models.BooleanField(default=False, verbose_name='active')),
                ('is_private', models.BooleanField(default=False, verbose_name='private')),
                ('is_ban', models.BooleanField(default=False, verbose_name='ban')),
                ('email', models.EmailField(max_length=254, null=True, unique=True, verbose_name='email address')),
                ('phone', models.CharField(max_length=11, null=True, unique=True, verbose_name='mobile number')),
                ('fullname', models.CharField(max_length=128, null=True, verbose_name='full name')),
                ('username', models.CharField(max_length=26, unique=True, verbose_name='username')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to=app_users.models.user_avatar_upload_path)),
                ('header', models.ImageField(blank=True, null=True, upload_to=app_users.models.user_header_upload_path)),
                ('bio', models.CharField(blank=True, max_length=256, null=True, verbose_name='tweeter bio')),
                ('birth_date', models.DateField(verbose_name='birth date')),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'ordering': ('-date_joined',),
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=django.contrib.postgres.indexes.HashIndex(fields=['phone'], name='app_users_u_phone_c5ebc4_hash'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=django.contrib.postgres.indexes.HashIndex(fields=['email'], name='app_users_u_email_d98f98_hash'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=django.contrib.postgres.indexes.HashIndex(fields=['username'], name='app_users_u_usernam_3aa7c7_hash'),
        ),
    ]
