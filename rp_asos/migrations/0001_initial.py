# Generated by Django 2.1 on 2018-10-30 08:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [("rp_redcap", "0019_lead_and_nomination_name")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=None,
            state_operations=[
                migrations.CreateModel(
                    name="Hospital",
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
                        ("name", models.CharField(max_length=200)),
                        ("data_access_group", models.CharField(max_length=200)),
                        ("rapidpro_flow", models.CharField(max_length=200)),
                        (
                            "hospital_lead_name",
                            models.CharField(max_length=200),
                        ),
                        ("hospital_lead_urn", models.CharField(max_length=200)),
                        (
                            "nomination_name",
                            models.CharField(
                                blank=True, max_length=200, null=True
                            ),
                        ),
                        (
                            "nomination_urn",
                            models.CharField(
                                blank=True, max_length=200, null=True
                            ),
                        ),
                        (
                            "project",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="hospitals",
                                to="rp_redcap.Project",
                            ),
                        ),
                    ],
                ),
                migrations.CreateModel(
                    name="PatientRecord",
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
                        ("record_id", models.CharField(max_length=30)),
                        ("date", models.DateField()),
                        (
                            "pre_operation_status",
                            models.CharField(
                                choices=[
                                    ("0", "Incomplete"),
                                    ("1", "Unverified"),
                                    ("2", "Complete"),
                                ],
                                default="0",
                                max_length=1,
                            ),
                        ),
                        (
                            "post_operation_status",
                            models.CharField(
                                choices=[
                                    ("0", "Incomplete"),
                                    ("1", "Unverified"),
                                    ("2", "Complete"),
                                ],
                                default="0",
                                max_length=1,
                            ),
                        ),
                        (
                            "project",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="patients",
                                to="rp_redcap.Project",
                            ),
                        ),
                    ],
                ),
                migrations.CreateModel(
                    name="PatientValue",
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
                        ("name", models.CharField(max_length=200)),
                        ("value", models.TextField(null=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        (
                            "patient",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="values",
                                to="rp_asos.PatientRecord",
                            ),
                        ),
                    ],
                ),
            ],
        )
    ]