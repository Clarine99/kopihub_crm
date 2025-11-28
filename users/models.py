from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    CASHIER = "cashier", "Cashier"
    ADMIN = "admin", "Admin"


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CASHIER,
    )

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"
