# Generated by Django 2.1 on 2018-09-26 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("sidekick", "0002_organization_users")]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="engage_token",
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="organization",
            name="engage_url",
            field=models.URLField(null=True),
        ),
    ]
