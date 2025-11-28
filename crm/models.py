from django.db import models
from django.utils import timezone

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

    def refresh_status_by_date(self):
        today = timezone.localdate()
        if self.status != MembershipStatus.BLOCKED and today > self.end_date:
            self.status = MembershipStatus.EXPIRED
            self.save(update_fields=['status'])

    def _next_cycle_number(self):
        last_cycle = self.cycles.order_by('-cycle_number').first()
        return (last_cycle.cycle_number + 1) if last_cycle else 1

    def active_cycle(self):
        return self.cycles.filter(is_active=True).order_by('-cycle_number').first()

    def open_cycle(self):
        existing = self.active_cycle()
        if existing:
            return existing
        return StampCycle.objects.create(membership=self, cycle_number=self._next_cycle_number())

    def award_stamp(self, *, transaction_amount=None, note=""):
        """
        Grant a new stamp if the transaction meets the configured minimum amount.
        Automatically closes the current cycle and opens the next one when the
        reward threshold is reached, issuing a reward stamp to mark completion.
        """
        settings = ProgramSettings.current()
        if transaction_amount is not None and transaction_amount < settings.min_transaction_amount:
            return None

        cycle = self.open_cycle()
        stamp = cycle.add_stamp(note=note)
        earned_count = cycle.stamps.filter(is_reward=False).count()

        if earned_count >= settings.stamps_per_reward:
            reward_stamp = cycle.add_stamp(is_reward=True, note=settings.reward_label)
            cycle.close()
            self.open_cycle()
            return reward_stamp

        return stamp

    def seed_welcome_reward(self, note="Welcome reward"):
        cycle = self.open_cycle()
        reward_stamp = cycle.add_stamp(is_reward=True, note=note)
        return reward_stamp

    def __str__(self):
        return f"{self.card_number} - {self.customer.name}"


class ProgramSettings(TimeStampedModel):
    min_transaction_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stamps_per_reward = models.PositiveIntegerField(default=10)
    reward_label = models.CharField(max_length=100, default="Reward")

    @classmethod
    def current(cls):
        settings = cls.objects.order_by('-created_at').first()
        if not settings:
            settings = cls.objects.create()
        return settings

    def __str__(self):
        return f"Reward after {self.stamps_per_reward} stamps"


class StampCycle(TimeStampedModel):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="cycles")
    cycle_number = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("membership", "cycle_number")
        ordering = ["membership", "cycle_number"]

    def add_stamp(self, *, is_reward=False, note=""):
        return Stamp.objects.create(
            membership=self.membership,
            cycle=self,
            is_reward=is_reward,
            note=note,
        )

    def close(self):
        if self.is_active:
            self.is_active = False
            self.closed_at = timezone.now()
            self.save(update_fields=["is_active", "closed_at"])

    def __str__(self):
        return f"Cycle {self.cycle_number} for {self.membership}"


class Stamp(TimeStampedModel):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="stamps")
    cycle = models.ForeignKey(StampCycle, on_delete=models.CASCADE, related_name="stamps")
    is_reward = models.BooleanField(default=False)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{'Reward' if self.is_reward else 'Stamp'} for {self.membership}"
            
# Create your models here.
