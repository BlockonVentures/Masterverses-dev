# Generated by Django 5.1.1 on 2024-12-21 11:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_app', '0015_cards_description_cards_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyReward',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.PositiveIntegerField()),
                ('points', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='UserDailyReward',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_day', models.PositiveIntegerField(default=1)),
                ('last_claimed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='user_daily_reward', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BoosterClaim',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('claim_type', models.CharField(max_length=50)),
                ('claim_at', models.DateTimeField(auto_now_add=True)),
                ('end_time', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'claim_at')},
            },
        ),
    ]
