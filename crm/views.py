from decimal import Decimal

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Customer, Membership, ProgramSettings, RewardType
from .serializers import (
    CustomerSerializer,
    MembershipSerializer,
    ProgramSettingsSerializer,
    StampSerializer,
)
from .services import award_stamp_for_transaction, redeem_reward_stamp, seed_initial_cycle


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.select_related("customer").all()
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        membership = serializer.save()
        seed_initial_cycle(membership)

    @action(detail=False, methods=["get"], url_path="lookup")
    def lookup(self, request):
        identifier = request.query_params.get("q")
        if not identifier:
            return Response({"detail": "q is required"}, status=status.HTTP_400_BAD_REQUEST)

        membership = (
            Membership.objects.select_related("customer")
            .filter(card_number__iexact=identifier)
            .first()
        )
        if membership is None:
            membership = (
                Membership.objects.select_related("customer")
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
            return Response(
                {"detail": "transaction_amount required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        stamp = redeem_reward_stamp(membership, reward_type)
        if not stamp:
            return Response({"detail": "No reward available"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(StampSerializer(stamp).data)


class ProgramSettingsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        settings = ProgramSettings.get_solo()
        serializer = ProgramSettingsSerializer(settings)
        return Response(serializer.data)

    def create(self, request):
        if not request.user.is_staff:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        settings = ProgramSettings.get_solo()
        serializer = ProgramSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
