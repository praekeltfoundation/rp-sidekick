# Generated by Django 2.2.2 on 2019-06-25 08:16

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [("sidekick", "0010_modify-consent-body")]

    operations = [
        migrations.CreateModel(
            name="Recruitment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False)),
                ("term_and_conditions", models.TextField()),
                ("rapidpro_flow_uuid", models.UUIDField()),
                ("rapidpro_pin_key_name", models.CharField(max_length=30)),
                ("rapidpro_group_name", models.CharField(max_length=30)),
                (
                    "org",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="campaigns",
                        to="sidekick.Organization",
                    ),
                ),
            ],
        )
    ]