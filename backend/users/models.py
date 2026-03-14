from django.contrib.auth.models import AbstractUser
from django.db import models

ROLE_USER  = 'USER'
ROLE_STAFF = 'STAFF'
ROLE_ADMIN = 'ADMIN'

ROLE_CHOICES = [
    (ROLE_USER,  'Student'),
    (ROLE_STAFF, 'Security Staff'),
    (ROLE_ADMIN, 'Administrator'),
]


class User(AbstractUser):
    """Custom user with a 3-tier role system: USER / STAFF / ADMIN."""
    first_name = None  # type: ignore[assignment]
    last_name  = None  # type: ignore[assignment]

    role       = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_USER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['username']

    @property
    def is_staff_role(self) -> bool:
        return self.role in (ROLE_STAFF, ROLE_ADMIN)

    @property
    def is_admin_role(self) -> bool:
        return self.role == ROLE_ADMIN

    @property
    def role_label(self) -> str:
        return {
            ROLE_USER:  'Student',
            ROLE_STAFF: 'Security Staff',
            ROLE_ADMIN: 'Administrator',
        }.get(self.role, self.role)

    def __str__(self) -> str:
        return self.username
