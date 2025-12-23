from decimal import Decimal

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date

from .models import Customer, Membership, MembershipCard, MembershipStatus, ProgramSettings, RewardType, Stamp
from .serializers import CustomerSerializer, MembershipCardSerializer, MembershipSerializer, StampSerializer
from .services import award_stamp_for_transaction
from users.permissions import IsAdminUserRole, IsCashierOrAdminRole


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsCashierOrAdminRole]


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.select_related("customer").prefetch_related("cycles__stamps").all()
    serializer_class = MembershipSerializer

    def get_permissions(self):
        admin_only_actions = {"create", "update", "partial_update", "destroy"}
        if self.action in admin_only_actions:
            permission_classes = [IsAdminUserRole]
        else:
            permission_classes = [IsCashierOrAdminRole]
        return [perm() for perm in permission_classes]

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Direct membership creation disabled. Use activate-card."},
            status=status.HTTP_403_FORBIDDEN,
        )

    @action(detail=False, methods=["get"], url_path="lookup")
    def lookup(self, request):
        identifier = request.query_params.get("q")
        if not identifier:
            return Response({"detail": "q is required"}, status=status.HTTP_400_BAD_REQUEST)
        # normalize common typos such as trailing slashes/spaces
        identifier = identifier.strip().strip("/")

        membership = (
            Membership.objects.select_related("customer")
            .prefetch_related("cycles__stamps")
            .filter(card_number__iexact=identifier)
            .first()
        )
        if membership is None:
            membership = (
                Membership.objects.select_related("customer")
                .prefetch_related("cycles__stamps")
                .filter(customer__phone__iexact=identifier)
                .order_by("-start_date")
                .first()
            )
        if membership is None:
            try:
                card = (
                    MembershipCard.objects.select_related("membership__customer")
                    .prefetch_related("membership__cycles__stamps")
                    .get(public_id=identifier)
                )
                membership = card.membership
            except (MembershipCard.DoesNotExist, ValueError, ValidationError):
                membership = None
        if membership is None:
            return Response({"detail": "Membership not found"}, status=status.HTTP_404_NOT_FOUND)

        membership.refresh_status_by_date()
        serializer = self.get_serializer(membership)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="activate-card")
    def activate_card(self, request):
        card_number = request.data.get("card_number")
        public_id = request.data.get("public_id")
        name = request.data.get("name")
        phone = request.data.get("phone")
        email = request.data.get("email")

        if not (card_number or public_id):
            return Response({"detail": "card_number or public_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not (name and phone):
            return Response({"detail": "name and phone are required"}, status=status.HTTP_400_BAD_REQUEST)

        card = None
        if card_number:
            card = MembershipCard.objects.filter(card_number=card_number).first()
        if card is None and public_id:
            card = MembershipCard.objects.filter(public_id=public_id).first()
        if card is None:
            return Response({"detail": "Card not found"}, status=status.HTTP_404_NOT_FOUND)
        if card.is_assigned or card.membership:
            return Response({"detail": "Card already assigned"}, status=status.HTTP_400_BAD_REQUEST)

        customer, created = Customer.objects.get_or_create(
            phone=phone,
            defaults={"name": name, "email": email},
        )
        if not created:
            updated = False
            if name and not customer.name:
                customer.name = name
                updated = True
            if email and not customer.email:
                customer.email = email
                updated = True
            if updated:
                customer.save(update_fields=["name", "email"])

        membership = Membership.create_new(
            customer=customer,
            card=card,
        )
        serializer = self.get_serializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="add-stamp")
    def add_stamp(self, request, pk=None):
        membership = self.get_object()
        amount = request.data.get("transaction_amount")
        receipt = request.data.get("pos_receipt_number")
        if amount is None:
            return Response({"detail": "transaction_amount required"}, status=status.HTTP_400_BAD_REQUEST)
        if receipt and Stamp.objects.filter(pos_receipt_number=receipt).exists():
            return Response({"detail": "pos_receipt_number already used"}, status=status.HTTP_400_BAD_REQUEST)

        stamp = award_stamp_for_transaction(
            membership,
            transaction_amount=Decimal(str(amount)),
            pos_receipt_number=receipt,
        )
        if stamp is None:
            return Response({"detail": "No stamp awarded"}, status=status.HTTP_200_OK)
        return Response(StampSerializer(stamp).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="redeem")
    def redeem_reward(self, request, pk=None):
        membership = self.get_object()
        reward_type = request.data.get("reward_type")
        if reward_type not in [RewardType.FREE_DRINK, RewardType.VOUCHER_50K]:
            return Response({"detail": "Invalid reward_type"}, status=status.HTTP_400_BAD_REQUEST)

        stamp = (
            Stamp.objects.filter(
                cycle__membership=membership,
                reward_type=reward_type,
                redeemed_at__isnull=True,
            )
            .order_by("cycle__cycle_number", "number")
            .first()
        )
        if not stamp:
            return Response({"detail": "No reward available"}, status=status.HTTP_400_BAD_REQUEST)

        stamp.mark_redeemed()
        return Response(StampSerializer(stamp).data)

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        membership = self.get_object()
        serializer = self.get_serializer(membership)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="history-summary")
    def history_summary(self, request, pk=None):
        membership = self.get_object()
        cycles = membership.cycles.order_by("cycle_number")
        active_cycle = cycles.filter(is_closed=False).last()
        latest_cycle = cycles.last()
        cycle = active_cycle or latest_cycle

        if cycle is None:
            data = {
                "membership_id": membership.id,
                "cycle_number": None,
                "stamp_count": 0,
                "is_full": False,
            }
            return Response(data)

        data = {
            "membership_id": membership.id,
            "cycle_number": cycle.cycle_number,
            "stamp_count": cycle.stamp_count,
            "is_full": cycle.is_full,
        }
        return Response(data)


class MembershipCardViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = MembershipCard.objects.all()
    serializer_class = MembershipCardSerializer
    permission_classes = [IsCashierOrAdminRole]


class ProgramSettingsViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUserRole]

    def list(self, request):
        settings = ProgramSettings.get_solo()
        data = {
            "membership_fee": settings.membership_fee,
            "membership_duration_months": settings.membership_duration_months,
            "discount_percent": settings.discount_percent,
            "min_amount_for_stamp": settings.min_amount_for_stamp,
            "reward_stamp_1_type": settings.reward_stamp_1_type,
            "reward_stamp_10_type": settings.reward_stamp_10_type,
        }
        return Response(data)

    def create(self, request):
        settings = ProgramSettings.get_solo()
        for field in [
            "membership_fee",
            "membership_duration_months",
            "discount_percent",
            "min_amount_for_stamp",
            "reward_stamp_1_type",
            "reward_stamp_10_type",
        ]:
            if field in request.data:
                setattr(settings, field, request.data[field])
        settings.save()
        return self.list(request)


class SummaryReportView(APIView):
    permission_classes = [IsCashierOrAdminRole]

    def get(self, request):
        start_param = request.query_params.get("from")
        end_param = request.query_params.get("to")
        try:
            start_date = parse_date(start_param) if start_param else None
        except ValueError:
            start_date = None
        try:
            end_date = parse_date(end_param) if end_param else None
        except ValueError:
            end_date = None
        if start_param and not start_date:
            return Response({"detail": "Invalid from date"}, status=status.HTTP_400_BAD_REQUEST)
        if end_param and not end_date:
            return Response({"detail": "Invalid to date"}, status=status.HTTP_400_BAD_REQUEST)

        memberships = Membership.objects.all()
        if start_date:
            memberships = memberships.filter(created_at__date__gte=start_date)
        if end_date:
            memberships = memberships.filter(created_at__date__lte=end_date)

        redeemed_stamps = Stamp.objects.filter(redeemed_at__isnull=False)
        if start_date:
            redeemed_stamps = redeemed_stamps.filter(redeemed_at__date__gte=start_date)
        if end_date:
            redeemed_stamps = redeemed_stamps.filter(redeemed_at__date__lte=end_date)

        data = {
            "active_members": memberships.filter(status=MembershipStatus.ACTIVE).count(),
            "expired_members": memberships.filter(status=MembershipStatus.EXPIRED).count(),
            "free_drink_used": redeemed_stamps.filter(reward_type=RewardType.FREE_DRINK).count(),
            "voucher_used": redeemed_stamps.filter(reward_type=RewardType.VOUCHER_50K).count(),
        }
        return Response(data)


class RewardReportView(APIView):
    permission_classes = [IsCashierOrAdminRole]

    def get(self, request):
        start_param = request.query_params.get("from")
        end_param = request.query_params.get("to")
        try:
            start_date = parse_date(start_param) if start_param else None
        except ValueError:
            start_date = None
        try:
            end_date = parse_date(end_param) if end_param else None
        except ValueError:
            end_date = None
        if start_param and not start_date:
            return Response({"detail": "Invalid from date"}, status=status.HTTP_400_BAD_REQUEST)
        if end_param and not end_date:
            return Response({"detail": "Invalid to date"}, status=status.HTTP_400_BAD_REQUEST)

        used = Stamp.objects.filter(redeemed_at__isnull=False)
        unused = Stamp.objects.filter(redeemed_at__isnull=True)
        if start_date:
            used = used.filter(redeemed_at__date__gte=start_date)
            unused = unused.filter(created_at__date__gte=start_date)
        if end_date:
            used = used.filter(redeemed_at__date__lte=end_date)
            unused = unused.filter(created_at__date__lte=end_date)

        data = {
            "free_drink_used": used.filter(reward_type=RewardType.FREE_DRINK).count(),
            "free_drink_unused": unused.filter(reward_type=RewardType.FREE_DRINK).count(),
            "voucher_used": used.filter(reward_type=RewardType.VOUCHER_50K).count(),
            "voucher_unused": unused.filter(reward_type=RewardType.VOUCHER_50K).count(),
        }
        return Response(data)
