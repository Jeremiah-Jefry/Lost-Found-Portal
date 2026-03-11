from django.db import models
from django.contrib.auth import get_user_model
from PIL import Image
import io
from django.core.files.base import ContentFile

User = get_user_model()

class Item(models.Model):
    STATUS_CHOICES = (
        ('LOST', 'Lost'),
        ('FOUND', 'Found'),
    )
    
    HANDOVER_CHOICES = (
        ('LEFT_AT_LOCATION', 'Left at Location'),
        ('WITH_FINDER', 'With Finder (Me)'),
        ('SECURITY', 'Handed to Security/Staff'),
        ('RESOLVED', 'Resolved / Returned to Owner'),
    )

    CATEGORY_CHOICES = (
        ('ELECTRONICS', 'Electronics & Gadgets'),
        ('DOCUMENTS', 'IDs & Documents'),
        ('KEYS', 'Keys & Access Cards'),
        ('CLOTHING', 'Clothing & Bags'),
        ('OTHER', 'Other'),
    )

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='LOST')
    location_description = models.CharField(max_length=255, help_text="Where was it lost/found?")
    date_reported = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)
    
    # Handover Logic Details
    handover_status = models.CharField(max_length=20, choices=HANDOVER_CHOICES, blank=True, null=True)
    handover_details = models.TextField(blank=True, null=True, help_text="Specific details (e.g., 'Handed to guard Ramesh at Gate 1')")
    receiver_name = models.CharField(max_length=100, blank=True, null=True, help_text="Name of the person who received the item (Security/Staff)")
    receiver_contact = models.CharField(max_length=20, blank=True, null=True, help_text="Contact number of the receiver")
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_items')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.image:
            img = Image.open(self.image.path)
            
            # Set maximum dimensions
            max_size = (800, 800)
            
            # Only resize if the image actually exceeds the maximum dimensions
            if img.height > max_size[1] or img.width > max_size[0]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Overwrite the original image with the resized image
                img.save(self.image.path)

    def __str__(self):
        return f"[{self.status}] {self.title}"
