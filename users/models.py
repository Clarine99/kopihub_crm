from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model so AUTH_USER_MODEL points to a concrete class."""

    def __str__(self) -> str:
        return self.get_username()
