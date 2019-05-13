# Generated by Django 2.1.7 on 2019-05-13 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("rp_asos", "0007_add_total_eligible_to_screeningrecord")]

    operations = [
        migrations.RemoveField(model_name="screeningrecord", name="week_day_1"),
        migrations.RemoveField(model_name="screeningrecord", name="week_day_2"),
        migrations.RemoveField(model_name="screeningrecord", name="week_day_3"),
        migrations.RemoveField(model_name="screeningrecord", name="week_day_4"),
        migrations.RemoveField(model_name="screeningrecord", name="week_day_5"),
        migrations.AlterField(
            model_name="screeningrecord",
            name="date",
            field=models.DateField(null=True),
        ),
    ]