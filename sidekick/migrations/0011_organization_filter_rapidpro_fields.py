# Generated by Django 3.2.14 on 2023-09-25 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sidekick', '0010_modify-consent-body'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='filter_rapidpro_fields',
            field=models.CharField(max_length=4000, null=True),
        ),
    ]
