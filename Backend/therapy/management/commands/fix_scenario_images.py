# management/commands/fix_scenario_images.py
"""
Django management command to fix ScenarioImage entries so their image field matches the actual file in the media folder.
- For each ScenarioImage, tries to find a file in MEDIA_ROOT/scenarios/ with the scenario's title (case-insensitive) and any supported extension.
- Updates the image field if a matching file is found.
"""

import os
from django.core.management.base import BaseCommand
from django.conf import settings
from therapy.models import ScenarioImage

SUPPORTED_EXTS = [".jpg", ".jpeg", ".png", ".webp", ".avif"]

class Command(BaseCommand):
    help = "Fix ScenarioImage image fields to match actual files in media folder."

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        scenarios_dir = os.path.join(media_root, "scenarios")
        if not os.path.isdir(scenarios_dir):
            self.stderr.write(f"Scenarios directory not found: {scenarios_dir}")
            return

        updated = 0
        for scenario in ScenarioImage.objects.all():
            base = scenario.title.lower().replace(" ", "_")
            found = None
            for ext in SUPPORTED_EXTS:
                fname = f"{base}{ext}"
                fpath = os.path.join(scenarios_dir, fname)
                if os.path.isfile(fpath):
                    found = f"scenarios/{fname}"
                    break
            if found:
                if scenario.image.name != found:
                    scenario.image.name = found
                    scenario.save(update_fields=["image"])
                    self.stdout.write(f"Updated {scenario.title}: {found}")
                    updated += 1
            else:
                self.stderr.write(f"No file found for {scenario.title}")
        self.stdout.write(f"Done. Updated {updated} ScenarioImage entries.")
