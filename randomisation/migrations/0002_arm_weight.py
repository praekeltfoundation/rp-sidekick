# Generated by Django 4.2.11 on 2024-04-23 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("randomisation", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="arm",
            name="weight",
            field=models.IntegerField(default=1),
        ),
    ]
