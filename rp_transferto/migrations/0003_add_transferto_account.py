# Generated by Django 2.1.2 on 2019-02-26 08:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sidekick", "0004_increase_engage_token_size"),
        ("rp_transferto", "0002_add_latest_in_meta_for_msisdn_cache"),
    ]

    operations = [
        migrations.CreateModel(
            name="TransferToAccount",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("login", models.CharField(max_length=200)),
                ("token", models.CharField(max_length=200)),
                ("apikey", models.CharField(max_length=200)),
                ("apisecret", models.CharField(max_length=200)),
                (
                    "org",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transferto_account",
                        to="sidekick.Organization",
                    ),
                ),
            ],
        )
    ]