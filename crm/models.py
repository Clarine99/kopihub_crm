from django.db import models
from django.utils import timezone
from datetime import timedelta

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Customer(TimeStampedModel):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.name} {self.phone}"
    
class MembershipStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    BLOCKED = "blocked", "Blocked"

class Membership(TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='memberships')
    card_number = models.CharField(max_length=50, unique=True)

    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=MembershipStatus.choices,
        default=MembershipStatus.ACTIVE,
    )
    def is_active(self):
        today = timezone.localdate()
        return self.status == "active" and self.start_date <= today <= self.end_date  
    
    def refresh_status_by_date (self):
        today = timezone.localdate()
        if self.status != MembershipStatus.BLOCKED and today > self.end_date:
            self.status = MembershipStatus.EXPIRED
            self.save(update_fields=['status'])
    def __str__(self):
        return f"{self.card_number} - {self.customer.name}"
            
# Create your models here.
