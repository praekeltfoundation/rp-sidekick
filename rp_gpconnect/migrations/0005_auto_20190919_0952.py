# Generated by Django 2.2.3 on 2019-09-19 09:52

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("rp_gpconnect", "0004_auto_20190804_1637")]

    operations = [
        migrations.AlterField(
            model_name="contactimport",
            name="file",
            field=models.FileField(
                upload_to="uploads/gpconnect/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["csv"]
                    )
                ],
            ),
        )
    ]
