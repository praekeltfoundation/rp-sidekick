# Generated by Django 2.1.7 on 2019-04-30 06:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("rp_asos", "0003_screeningrecord")]

    operations = [
        migrations.AddField(
            model_name="hospital",
            name="tz_code",
            field=models.CharField(default="CAT", max_length=10),
        )
    ]