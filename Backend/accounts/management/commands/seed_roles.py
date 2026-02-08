from __future__ import annotations
from django.core.management.base import BaseCommand
from accounts.models import Role

DEFAULT_ROLES = [
    ("admin", "Admin"),
    ("therapist", "Therapist"),
    ("parent", "Parent"),
    ("child", "Child"),
]

class Command(BaseCommand):
    help = "Seed core RBAC roles for DHYAN"

    def handle(self, *args, **options):
        created = 0
        for slug, name in DEFAULT_ROLES:
            obj, was_created = Role.objects.get_or_create(
                slug=slug,
                defaults={"name": name}
            )
            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Roles seeded. created={created}, total={Role.objects.count()}"
            )
        )
