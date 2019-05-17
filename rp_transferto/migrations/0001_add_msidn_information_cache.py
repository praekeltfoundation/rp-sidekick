# Generated by Django 2.1.2 on 2018-10-26 15:05

import django.contrib.postgres.fields.jsonb
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MsisdnInformation",
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
                ("msisdn", models.CharField(max_length=200)),
                ("data", django.contrib.postgres.fields.jsonb.JSONField()),
                ("timestamp", models.DateTimeField(default=django.utils.timezone.now)),
            ],
        )
    ]
