# Generated by Django 2.1 on 2018-09-26 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("sidekick", "0003_add_engage_creds")]

    operations = [
        migrations.AlterField(
            model_name="organization",
            name="engage_token",
            field=models.CharField(max_length=1000, null=True),
        )
    ]
