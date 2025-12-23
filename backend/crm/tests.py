from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import UserRole

from .models import Customer, Membership, MembershipCard, ProgramSettings, RewardType, StampCycle
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

    def test_membership_card_auto_generates_number(self):
        card = MembershipCard.objects.create()
        self.assertTrue(card.card_number)
        self.assertTrue(card.card_number.startswith("CARD-"))


class MembershipCardApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="cashier",
            password="pass1234",
            role=UserRole.CASHIER,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_create_card_generates_number(self):
        response = self.client.post(reverse("cards-list"), data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["card_number"].startswith("CARD-"))

    def test_card_qr_returns_png(self):
        card = MembershipCard.objects.create()
        response = self.client.get(reverse("cards-qr"), data={"public_id": str(card.public_id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/png")


class MembershipHistoryApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="cashier-history",
            password="pass1234",
            role=UserRole.CASHIER,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.customer = Customer.objects.create(name="History Tester", phone="0800000001")
        today = timezone.localdate()
        self.membership = Membership.objects.create(
            customer=self.customer,
            card_number="CARD-HIST",
            start_date=today,
            end_date=today + timedelta(days=90),
        )

    def test_history_returns_membership_detail(self):
        response = self.client.get(reverse("memberships-history", kwargs={"pk": self.membership.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.membership.id)

    def test_history_summary_returns_cycle_info(self):
        response = self.client.get(
            reverse("memberships-history-summary", kwargs={"pk": self.membership.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["membership_id"], self.membership.id)

    def test_history_summary_active_only(self):
        active_cycle = StampCycle.objects.create(
            membership=self.membership,
            cycle_number=1,
            is_closed=False,
        )
        StampCycle.objects.create(
            membership=self.membership,
            cycle_number=2,
            is_closed=True,
        )
        response = self.client.get(
            reverse("memberships-history-summary", kwargs={"pk": self.membership.id}),
            data={"active_only": "true"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["cycle_number"], active_cycle.cycle_number)

    def test_history_summary_lookup_by_public_id(self):
        card = MembershipCard.objects.create(
            card_number=self.membership.card_number,
            membership=self.membership,
            is_assigned=True,
        )
        response = self.client.get(
            reverse("memberships-history-summary-lookup"),
            data={"public_id": str(card.public_id)},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["membership_id"], self.membership.id)


class SummaryReportApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="cashier-report",
            password="pass1234",
            role=UserRole.CASHIER,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_summary_report_returns_counts(self):
        response = self.client.get(reverse("reports-summary"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("active_members", response.data)

    def test_summary_report_invalid_from_date(self):
        response = self.client.get(reverse("reports-summary"), data={"from": "2025-99-99"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RewardReportApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="cashier-reward-report",
            password="pass1234",
            role=UserRole.CASHIER,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_reward_report_returns_counts(self):
        response = self.client.get(reverse("reports-rewards"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("free_drink_used", response.data)

    def test_reward_report_invalid_to_date(self):
        response = self.client.get(reverse("reports-rewards"), data={"to": "invalid-date"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TransactionReportApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="cashier-transaction-report",
            password="pass1234",
            role=UserRole.CASHIER,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_transaction_report_returns_counts(self):
        response = self.client.get(reverse("reports-transactions"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("eligible_stamp_count", response.data)

    def test_transaction_daily_report_returns_list(self):
        response = self.client.get(reverse("reports-transactions-daily"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
