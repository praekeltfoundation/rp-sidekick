import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from momconnect.models import Clinic


class Command(BaseCommand):
    help = (
        "Import clinics from a CSV file and update or create them in the Clinic model"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file", type=str, help="Path to the CSV file containing clinic data"
        )

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        try:
            with Path(csv_file).open(newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    clinic, created = Clinic.objects.update_or_create(
                        value=row["value"],
                        defaults={
                            "code": row["code"],
                            "uid": row["uid"],
                            "name": row["name"],
                            "province": row["province"],
                            "location": row["location"],
                            "area_type": row["area_type"],
                            "unit_type": row["unit_type"],
                            "district": row["district"],
                            "municipality": row["municipality"],
                        },
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f"Created clinic: {clinic.name}")
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f"Updated clinic: {clinic.name}")
                        )
        except FileNotFoundError as e:
            raise CommandError(f"File '{csv_file}' does not exist.") from e
        except KeyError as e:
            raise CommandError(f"Missing required column in CSV: {e}") from e
        except Exception as e:
            raise CommandError(f"An error occurred: {e}") from e
