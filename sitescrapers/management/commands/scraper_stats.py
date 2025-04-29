from django.core.management.base import BaseCommand
from django.db.models import Max, Min, Q  # Import Min, Max

# Import your models from the sitescrapers app
from sitescrapers.models import Property


class Command(BaseCommand):
    help = "Displays statistics about scraped Property records."

    def handle(self, *args, **options):
        self.stdout.write("Calculating Scraper Statistics...")
        self.stdout.write("-" * 20)

        # --- Timestamps ---
        timestamps = Property.objects.aggregate(
            first_created=Min("created_at"),
            last_created=Max("created_at"),
            last_updated=Max("updated_at"),
        )
        first_created = timestamps.get("first_created") or "N/A"
        last_created = timestamps.get("last_created") or "N/A"
        last_updated = timestamps.get("last_updated") or "N/A"
        self.stdout.write(f"- First Record Created: {first_created}")
        self.stdout.write(f"- Last Record Created:  {last_created}")
        self.stdout.write(f"- Last Record Updated:  {last_updated}")
        self.stdout.write("-" * 20)

        # --- Counts (using Python iteration) ---
        self.stdout.write("Calculating counts (using Python iteration)...")
        all_properties_qs = Property.objects.only("images", "floorplans").iterator()

        total_properties_scraped = 0
        total_photos_scraped = 0
        properties_with_floorplans = 0
        total_floorplans_scraped = 0

        for prop in all_properties_qs:
            total_properties_scraped += 1
            if prop.images:
                total_photos_scraped += len(prop.images)
            if prop.floorplans:
                properties_with_floorplans += 1
                total_floorplans_scraped += len(prop.floorplans)

        # --- Output the results ---
        self.stdout.write(f"- Total Properties Scraped: {total_properties_scraped}")
        self.stdout.write(f"- Total Photos Scraped: {total_photos_scraped}")
        self.stdout.write(
            f"- Properties with Scraped Floorplans: {properties_with_floorplans}"
        )
        self.stdout.write(f"- Total Scraped Floorplans: {total_floorplans_scraped}")

        self.stdout.write("-" * 20)
        self.stdout.write(
            self.style.SUCCESS("Finished calculating scraper statistics.")
        )
