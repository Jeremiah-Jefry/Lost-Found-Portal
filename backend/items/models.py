import os
import uuid
from django.db import models
from django.conf import settings
from PIL import Image


CATEGORY_CHOICES = [
    ('ELECTRONICS', 'Electronics & Gadgets'),
    ('DOCUMENTS',   'IDs & Documents'),
    ('KEYS',        'Keys & Access Cards'),
    ('CLOTHING',    'Clothing & Bags'),
    ('OTHER',       'Other'),
]

STATUS_CHOICES = [
    ('LOST',  'Lost'),
    ('FOUND', 'Found'),
]

RESOLUTION_CHOICES = [
    ('OPEN',     'Open'),
    ('SECURED',  'Secured'),
    ('RETURNED', 'Returned to Owner'),
]

HANDOVER_CHOICES = [
    ('LEFT_AT_LOCATION', 'Left at Location'),
    ('WITH_FINDER',      'With Finder'),
    ('SECURITY',         'Handed to Security'),
]

LOG_ACTION_CHOICES = [
    ('CREATED',          'Created'),
    ('EDITED',           'Edited'),
    ('STATUS_CHANGED',   'Status Changed'),
    ('RESOLVED',         'Resolved'),
    ('MATCH_FOUND',      'Match Found'),
    ('HANDOVER_UPDATED', 'Handover Updated'),
]


def upload_to(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return f'uploads/{uuid.uuid4().hex}.{ext}'


def compress_image(path: str) -> None:
    ext = path.rsplit('.', 1)[-1].lower()
    if ext == 'gif':
        return
    try:
        with Image.open(path) as img:
            max_w = 1024
            if img.width > max_w:
                ratio    = max_w / img.width
                new_size = (max_w, max(1, int(img.height * ratio)))
                img      = img.resize(new_size, Image.LANCZOS)
            if ext in ('jpg', 'jpeg'):
                img = img.convert('RGB')
                img.save(path, format='JPEG', optimize=True, quality=70)
            elif ext == 'webp':
                img.save(path, format='WEBP', quality=70)
            else:
                img.save(path, format='PNG', optimize=True)
    except Exception:
        pass


class Item(models.Model):
    title             = models.CharField(max_length=200)
    description       = models.TextField()
    status            = models.CharField(max_length=10,  choices=STATUS_CHOICES,     default='LOST',  db_index=True)
    category          = models.CharField(max_length=20,  choices=CATEGORY_CHOICES,   default='OTHER', db_index=True)
    location          = models.CharField(max_length=255, db_index=True)
    image             = models.ImageField(upload_to=upload_to, null=True, blank=True)

    resolution_status = models.CharField(max_length=20, choices=RESOLUTION_CHOICES,  default='OPEN',  db_index=True)
    handover_status   = models.CharField(max_length=20, choices=HANDOVER_CHOICES,    null=True, blank=True)
    handover_details  = models.TextField(null=True, blank=True)
    receiver_name     = models.CharField(max_length=100, null=True, blank=True)
    receiver_contact  = models.CharField(max_length=100, null=True, blank=True)

    date_reported     = models.DateTimeField(auto_now_add=True, db_index=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    reporter          = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='items',
    )

    class Meta:
        ordering = ['-date_reported']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image and hasattr(self.image, 'path'):
            try:
                compress_image(self.image.path)
            except Exception:
                pass

    @property
    def status_label(self) -> str:
        return 'Lost' if self.status == 'LOST' else 'Found'

    @property
    def category_label(self) -> str:
        return dict(CATEGORY_CHOICES).get(self.category, 'Other')

    @property
    def handover_label(self) -> str:
        return dict(HANDOVER_CHOICES).get(self.handover_status or '', '')

    @property
    def resolution_label(self) -> str:
        return dict(RESOLUTION_CHOICES).get(self.resolution_status, 'Open')

    def __str__(self) -> str:
        return f'[{self.status}] {self.title}'


class ItemLog(models.Model):
    item       = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='logs')
    actor      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    actor_role = models.CharField(max_length=10)
    action     = models.CharField(max_length=30, choices=LOG_ACTION_CHOICES)
    note       = models.TextField(null=True, blank=True)
    from_value = models.CharField(max_length=100, null=True, blank=True)
    to_value   = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def action_label(self) -> str:
        return dict(LOG_ACTION_CHOICES).get(self.action, self.action)

    @property
    def action_icon(self) -> str:
        return {
            'CREATED':          'fa-plus',
            'EDITED':           'fa-pen',
            'STATUS_CHANGED':   'fa-arrows-rotate',
            'RESOLVED':         'fa-check',
            'MATCH_FOUND':      'fa-link',
            'HANDOVER_UPDATED': 'fa-hand-holding',
        }.get(self.action, 'fa-circle')

    def __str__(self) -> str:
        return f'{self.action} on Item#{self.item_id} by {self.actor_id}'


class Match(models.Model):
    found_item  = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='found_matches')
    lost_item   = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='lost_matches')
    score       = models.IntegerField(default=0)
    is_reviewed = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('found_item', 'lost_item')]
        ordering        = ['-score', '-created_at']

    def __str__(self) -> str:
        return f'Match({self.found_item_id} ↔ {self.lost_item_id}, score={self.score})'
