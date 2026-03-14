import os
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from items.models import Item


class Command(BaseCommand):
    help = 'Delete image files for items reported more than 30 days ago.'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=30)
        old_items = Item.objects.filter(date_reported__lt=cutoff).exclude(image='')
        count = 0
        for item in old_items:
            if item.image and hasattr(item.image, 'path'):
                try:
                    if os.path.exists(item.image.path):
                        os.remove(item.image.path)
                        count += 1
                except Exception as e:
                    self.stderr.write(f'Could not delete {item.image.path}: {e}')
            item.image = None
            item.save(update_fields=['image'])
        self.stdout.write(self.style.SUCCESS(
            f'Removed images from {count} items older than 30 days.'
        ))
