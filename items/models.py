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

    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='LOST')
    location_description = models.CharField(max_length=255, help_text="Where was it lost/found?")
    date_reported = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)
    
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
