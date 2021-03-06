# Generated by Django 2.1 on 2018-08-16 06:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sidekick", "0001_create_organization"),
        ("rp_redcap", "0004_contact_new_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="org",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="projects",
                to="sidekick.Organization",
            ),
            preserve_default=False,
        )
    ]
