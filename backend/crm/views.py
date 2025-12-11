from decimal import Decimal

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Customer, Membership, ProgramSettings, RewardType, Stamp
from .serializers import CustomerSerializer, MembershipSerializer, StampSerializer
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
        admin_only_actions = {"update", "partial_update", "destroy"}
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

    @action(detail=False, methods=["get"], url_path="lookup")
    def lookup(self, request):
        identifier = request.query_params.get("q")
        if not identifier:
            return Response({"detail": "q is required"}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response({"detail": "Membership not found"}, status=status.HTTP_404_NOT_FOUND)

        membership.refresh_status_by_date()
        serializer = self.get_serializer(membership)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="add-stamp")
    def add_stamp(self, request, pk=None):
        membership = self.get_object()
        amount = request.data.get("transaction_amount")
        receipt = request.data.get("pos_receipt_number")
        if amount is None:
            return Response({"detail": "transaction_amount required"}, status=status.HTTP_400_BAD_REQUEST)

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
