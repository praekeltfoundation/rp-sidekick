# Generated by Django 2.1.7 on 2019-04-10 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("rp_asos", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="hospital",
            name="whatsapp_group_id",
            field=models.CharField(blank=True, max_length=200, null=True),
        )
    ]
