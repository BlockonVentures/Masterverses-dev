# Generated by Django 5.1.1 on 2024-10-24 07:58

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user_app", "0010_alter_tasks_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="Cards",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("number", models.PositiveIntegerField(default=1)),
                (
                    "card_type",
                    models.CharField(
                        choices=[
                            ("eternals", "Eternals"),
                            ("divine", "Divine"),
                            ("specials", "specials"),
                        ],
                        max_length=20,
                    ),
                ),
                ("points", models.PositiveIntegerField()),
            ],
        ),
    ]
