from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # We can add extra fields here later if needed (e.g., phone_number, department)
    pass
