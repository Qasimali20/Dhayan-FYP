"""
Management command to seed scenario images for the Scene Description game.
Creates sample scenarios with different difficulty levels.

Usage:
    python manage.py seed_scenarios
"""
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont

from therapy.models import ScenarioImage


class Command(BaseCommand):
    help = "Seed scenario images for Scene Description game"

    def create_placeholder_image(self, title: str, color: tuple, size: tuple = (400, 300)) -> ContentFile:
        """Create a simple placeholder image with text."""
        img = Image.new("RGB", size, color=color)
        draw = ImageDraw.Draw(img)
        
        # Add text
        text_bbox = draw.textbbox((0, 0), title)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        draw.text((x, y), title, fill=(255, 255, 255))
        
        # Save to BytesIO
        img_io = BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)
        
        return ContentFile(img_io.getvalue(), name=f"{title.lower().replace(' ', '_')}.png")

    def handle(self, *args, **options):
        self.stdout.write("Creating scenario images...")

        scenarios = [
            # Easy Level (Level 1)
            {
                "title": "Playground",
                "level": 1,
                "color": (100, 200, 100),  # Green
                "expected": "A playground with swings, slides, and children playing",
                "elements": ["playground", "swings", "slide", "children", "playing"],
            },
            {
                "title": "Kitchen",
                "level": 1,
                "color": (255, 200, 100),  # Orange
                "expected": "A kitchen with appliances and food items",
                "elements": ["kitchen", "stove", "refrigerator", "table", "food"],
            },
            {
                "title": "Library",
                "level": 1,
                "color": (150, 100, 200),  # Purple
                "expected": "A library with books and people reading",
                "elements": ["library", "books", "shelves", "people", "reading"],
            },
            # Medium Level (Level 2)
            {
                "title": "Market Scene",
                "level": 2,
                "color": (200, 100, 100),  # Reddish
                "expected": "A busy market with vendors, customers, fruits, vegetables, and various products",
                "elements": ["market", "vendors", "customers", "fruits", "vegetables", "stalls", "busy"],
            },
            {
                "title": "Beach",
                "level": 2,
                "color": (100, 180, 200),  # Light blue
                "expected": "A beach scene with sand, water, umbrellas, and people",
                "elements": ["beach", "sand", "water", "ocean", "people", "umbrellas", "sun"],
            },
            {
                "title": "School Classroom",
                "level": 2,
                "color": (200, 180, 100),  # Tan
                "expected": "A classroom with desks, a teacher, students, and educational materials",
                "elements": ["classroom", "desks", "teacher", "students", "board", "books", "learning"],
            },
            # Hard Level (Level 3)
            {
                "title": "Hospital Scene",
                "level": 3,
                "color": (200, 200, 200),  # Light gray
                "expected": "A hospital with doctors, nurses, patients, medical equipment, and multiple rooms with various activities",
                "elements": ["hospital", "doctors", "nurses", "patients", "medical_equipment", "care", "health", "rooms"],
            },
            {
                "title": "Restaurant",
                "level": 3,
                "color": (180, 120, 100),  # Brown
                "expected": "A restaurant with waiters, customers, tables, food, drinks, and a busy atmosphere",
                "elements": ["restaurant", "waiters", "customers", "tables", "food", "drinks", "kitchen", "service"],
            },
            {
                "title": "Park in Different Seasons",
                "level": 3,
                "color": (100, 150, 100),  # Green
                "expected": "A park showing different seasonal changes with trees, people, weather, and various activities",
                "elements": ["park", "trees", "seasons", "weather", "people", "activities", "nature", "changes"],
            },
        ]

        created_count = 0
        for scenario_data in scenarios:
            # Check if already exists
            if ScenarioImage.objects.filter(title=scenario_data["title"]).exists():
                self.stdout.write(f"  ⊘ {scenario_data['title']} (already exists)")
                continue

            # Create placeholder image
            image_content = self.create_placeholder_image(
                scenario_data["title"],
                scenario_data["color"],
            )

            # Create ScenarioImage
            scenario = ScenarioImage.objects.create(
                title=scenario_data["title"],
                level=scenario_data["level"],
                expected_description=scenario_data["expected"],
                key_elements=scenario_data["elements"],
                image=image_content,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ {scenario.title} (Level {scenario.level}) - ID: {scenario.id}"
                )
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Successfully created {created_count} scenarios!")
        )
