# Generated by Django 2.1 on 2018-08-31 06:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("rp_redcap", "0012_remove_project_reminder_limit")]

    operations = [
        migrations.RemoveField(model_name="survey", name="check_fields")
    ]