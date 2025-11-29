from datetime import timedelta

from django.db import models
from django.utils import timezone

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Customer(TimeStampedModel):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} {self.phone}"
    
class MembershipStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    BLOCKED = "blocked", "Blocked"


class Membership(TimeStampedModel):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="memberships"
    )
    card_number = models.CharField(max_length=50, unique=True)

    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=MembershipStatus.choices,
        default=MembershipStatus.ACTIVE,
    )

    @property
    def is_active(self):
        today = timezone.localdate()
        return self.status == MembershipStatus.ACTIVE and self.start_date <= today <= self.end_date

    def refresh_status_by_date(self):
        today = timezone.localdate()
        if self.status != MembershipStatus.BLOCKED and today > self.end_date:
            self.status = MembershipStatus.EXPIRED
            self.save(update_fields=["status"])

    def __str__(self):
        return f"{self.card_number} - {self.customer.name}"


class StampCycle(TimeStampedModel):
    membership = models.ForeignKey(
        Membership, on_delete=models.CASCADE, related_name="cycles"
    )
    cycle_number = models.PositiveIntegerField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("membership", "cycle_number")

    def __str__(self):
        return f"{self.membership.card_number} - Cycle {self.cycle_number}"

    @property
    def stamp_count(self) -> int:
        return self.stamps.count()

    @property
    def is_full(self) -> bool:
        return self.stamp_count >= 10


class RewardType(models.TextChoices):
    NONE = "none", "No Reward"
    FREE_DRINK = "free_drink", "Free Drink"
    VOUCHER_50K = "voucher_50k", "Voucher 50k"


class Stamp(TimeStampedModel):
    cycle = models.ForeignKey(StampCycle, on_delete=models.CASCADE, related_name="stamps")
    number = models.PositiveIntegerField()

    reward_type = models.CharField(
        max_length=20, choices=RewardType.choices, default=RewardType.NONE
    )
    redeemed_at = models.DateTimeField(blank=True, null=True)

    pos_receipt_number = models.CharField(max_length=100, blank=True, null=True)
    transaction_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )

    class Meta:
        unique_together = ("cycle", "number")

    def __str__(self):
        return f"Stamp {self.number} - {self.cycle}"

    @property
    def is_redeemed(self) -> bool:
        return self.redeemed_at is not None

    def mark_redeemed(self):
        if not self.is_redeemed:
            self.redeemed_at = timezone.now()
            self.save(update_fields=["redeemed_at"])


class ProgramSettings(TimeStampedModel):
    is_active = models.BooleanField(default=True)

    membership_fee = models.PositiveIntegerField(default=25000)
    membership_duration_months = models.PositiveIntegerField(default=3)

    discount_percent = models.PositiveIntegerField(default=10)
    min_amount_for_stamp = models.PositiveIntegerField(default=50000)

    reward_stamp_1_type = models.CharField(
        max_length=20, choices=RewardType.choices, default=RewardType.FREE_DRINK
    )
    reward_stamp_10_type = models.CharField(
        max_length=20, choices=RewardType.choices, default=RewardType.VOUCHER_50K
    )

    def __str__(self):
        return "Program Settings"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

