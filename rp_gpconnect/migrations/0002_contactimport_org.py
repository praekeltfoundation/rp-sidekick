# Generated by Django 2.2.3 on 2019-07-19 12:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sidekick', '0010_modify-consent-body'),
        ('rp_gpconnect', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactimport',
            name='org',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='sidekick.Organization'),
        ),
    ]