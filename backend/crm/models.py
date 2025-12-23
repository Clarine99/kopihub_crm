from datetime import timedelta
import uuid

from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Customer(TimeStampedModel):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.phone})"


class MembershipCard(TimeStampedModel):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    card_number = models.CharField(max_length=50, unique=True)
    is_assigned = models.BooleanField(default=False)
    membership = models.OneToOneField(
        "Membership",
        on_delete=models.SET_NULL,
        related_name="card",
        null=True,
        blank=True,
    )

    @staticmethod
    def generate_card_number() -> str:
        return f"CARD-{uuid.uuid4().hex[:10].upper()}"

    def save(self, *args, **kwargs):
        if not self.card_number:
            self.card_number = self.generate_card_number()
            while type(self).objects.filter(card_number=self.card_number).exists():
                self.card_number = self.generate_card_number()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.card_number} ({'assigned' if self.is_assigned else 'unassigned'})"


class MembershipStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    BLOCKED = "blocked", "Blocked"


class Membership(TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="memberships")
    card_number = models.CharField(max_length=50, unique=True, editable=False)

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=MembershipStatus.choices,
        default=MembershipStatus.ACTIVE,
    )

    def __str__(self) -> str:
        return f"{self.card_number} - {self.customer.name}"

    @property
    def is_active(self) -> bool:
        today = timezone.localdate()
        return self.status == MembershipStatus.ACTIVE and self.start_date <= today <= self.end_date

    def refresh_status_by_date(self) -> None:
        today = timezone.localdate()
        if self.status == MembershipStatus.BLOCKED:
            return
        if today > self.end_date:
            self.status = MembershipStatus.EXPIRED
            self.save(update_fields=["status"])

    @classmethod
    def create_new(
        cls,
        customer: "Customer",
        card: "MembershipCard",
        duration_months: int | None = None,
        start_date=None,
        end_date=None,
    ) -> "Membership":
        from .models import ProgramSettings  # local import to avoid circular dependency

        settings = ProgramSettings.get_solo()
        months = duration_months or settings.membership_duration_months

        start = start_date or timezone.localdate()
        computed_end = end_date or (start + timedelta(days=months * 30))

        with transaction.atomic():
            membership = cls.objects.create(
                customer=customer,
                card_number=card.card_number,
                start_date=start,
                end_date=computed_end,
                status=MembershipStatus.ACTIVE,
            )
            card.membership = membership
            card.is_assigned = True
            card.save(update_fields=["membership", "is_assigned"])
            cycle = StampCycle.objects.create(
                membership=membership,
                cycle_number=1,
                is_closed=False,
            )
            Stamp.objects.create(
                cycle=cycle,
                number=1,
                reward_type=settings.reward_stamp_1_type or RewardType.FREE_DRINK,
            )
            return membership


class StampCycle(TimeStampedModel):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="cycles")
    cycle_number = models.PositiveIntegerField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("membership", "cycle_number")

    def __str__(self) -> str:
        return f"{self.membership.card_number} - Cycle {self.cycle_number}"

    @property
    def stamp_count(self) -> int:
        return self.stamps.count()

    @property
    def is_full(self) -> bool:
        return self.stamp_count >= 10


class RewardType(models.TextChoices):
    NONE = "none", "No Reward"
    FREE_DRINK = "free_drink", "Free Americano/Latte"
    VOUCHER_50K = "voucher_50k", "Voucher Rp 50.000"


class Stamp(TimeStampedModel):
    cycle = models.ForeignKey(StampCycle, on_delete=models.CASCADE, related_name="stamps")
    number = models.PositiveIntegerField()

    reward_type = models.CharField(
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.NONE,
    )
    redeemed_at = models.DateTimeField(blank=True, null=True)

    pos_receipt_number = models.CharField(max_length=100, blank=True, null=True)
    transaction_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        unique_together = ("cycle", "number")
        constraints = [
            models.UniqueConstraint(
                fields=["pos_receipt_number"],
                condition=Q(pos_receipt_number__isnull=False),
                name="unique_receipt_number_when_present",
            )
        ]

    def __str__(self) -> str:
        return f"Stamp {self.number} - {self.cycle}"

    @property
    def is_redeemed(self) -> bool:
        return self.redeemed_at is not None

    def mark_redeemed(self) -> None:
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
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.FREE_DRINK,
    )
    reward_stamp_10_type = models.CharField(
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.VOUCHER_50K,
    )

    def __str__(self) -> str:
        return "Program Settings"

    @classmethod
    def get_solo(cls) -> "ProgramSettings":
        obj, _ = cls.objects.get_or_create(id=1)
        return obj


class AuditAction(models.TextChoices):
    ACTIVATE_CARD = "activate_card", "Activate Card"
    SCAN = "scan", "Scan"
    REDEEM = "redeem", "Redeem"
    REPLACE_CARD = "replace_card", "Replace Card"


class AuditLog(TimeStampedModel):
    action = models.CharField(max_length=30, choices=AuditAction.choices)
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    membership = models.ForeignKey(
        Membership,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    card = models.ForeignKey(
        MembershipCard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.action} ({self.created_at})"
