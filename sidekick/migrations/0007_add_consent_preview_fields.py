# Generated by Django 2.1.8 on 2019-05-23 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("sidekick", "0006_add_consent_model")]

    operations = [
        migrations.AddField(
            model_name="consent",
            name="body_text",
            field=models.CharField(
                blank=True,
                help_text="The text to display to the user while they're redirecting",
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name="consent",
            name="preview_description",
            field=models.CharField(
                blank=True,
                help_text="The description to display in the WhatsApp preview",
                max_length=65,
            ),
        ),
        migrations.AddField(
            model_name="consent",
            name="preview_image_url",
            field=models.URLField(
                blank=True,
                help_text="The URL of the imgae to display on the WhatsApp preview",
            ),
        ),
        migrations.AddField(
            model_name="consent",
            name="preview_title",
            field=models.CharField(
                blank=True,
                help_text="The title displayed on the WhatsApp preview and page",
                max_length=35,
            ),
        ),
        migrations.AddField(
            model_name="consent",
            name="preview_url",
            field=models.URLField(
                blank=True, help_text="The URL to display on the WhatsApp preview"
            ),
        ),
    ]