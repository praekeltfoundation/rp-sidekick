# Generated by Django 4.2.11 on 2024-05-06 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sidekick", "0013_groupmonitor"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="contentrepo_token",
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="organization",
            name="contentrepo_url",
            field=models.URLField(null=True),
        ),
    ]
