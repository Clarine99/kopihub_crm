from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import Customer, Membership, ProgramSettings, RewardType, StampCycle
from .serializers import MembershipSerializer
from .services import award_stamp_for_transaction


class AwardStampTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Tester", phone="0800000000")
        today = timezone.localdate()
        self.membership = Membership.objects.create(
            customer=self.customer,
            card_number="CARD123",
            start_date=today,
            end_date=today + timedelta(days=90),
        )
        ProgramSettings.get_solo()

    def test_award_first_stamp_sets_reward(self):
        stamp = award_stamp_for_transaction(self.membership, Decimal("60000"), "POS-1")
        self.assertIsNotNone(stamp)
        self.assertEqual(stamp.number, 1)
        self.assertEqual(stamp.reward_type, RewardType.FREE_DRINK)
        self.assertEqual(stamp.cycle.cycle_number, 1)
        self.assertFalse(stamp.cycle.is_closed)

    def test_cycle_closes_at_ten_and_new_cycle_starts(self):
        cycle = StampCycle.objects.create(membership=self.membership, cycle_number=1)
        for num in range(1, 10):
            cycle.stamps.create(number=num, reward_type=RewardType.NONE)

        tenth = award_stamp_for_transaction(self.membership, Decimal("60000"))
        self.assertEqual(tenth.number, 10)
        self.assertEqual(tenth.reward_type, ProgramSettings.get_solo().reward_stamp_10_type)
        tenth.refresh_from_db()
        cycle.refresh_from_db()
        self.assertTrue(cycle.is_closed)

        eleventh = award_stamp_for_transaction(self.membership, Decimal("60000"))
        self.assertEqual(eleventh.number, 1)
        self.assertEqual(eleventh.cycle.cycle_number, 2)

    def test_expired_membership_receives_no_stamp(self):
        self.membership.start_date = timezone.localdate() - timedelta(days=120)
        self.membership.end_date = timezone.localdate() - timedelta(days=1)
        self.membership.save(update_fields=["start_date", "end_date"])

        stamp = award_stamp_for_transaction(self.membership, Decimal("60000"))
        self.assertIsNone(stamp)

    def test_membership_serializer_sets_default_dates(self):
        serializer = MembershipSerializer(
            data={"customer_id": self.customer.id, "card_number": "CARD999"},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        membership = serializer.save()

        today = timezone.localdate()
        self.assertEqual(membership.start_date, today)
        self.assertEqual(
            membership.end_date,
            today + timedelta(days=ProgramSettings.get_solo().membership_duration_months * 30),
        )
