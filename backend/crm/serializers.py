from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import Customer, Membership, ProgramSettings, Stamp, StampCycle


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "email"]


class StampSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stamp
        fields = [
            "id",
            "number",
            "reward_type",
            "redeemed_at",
            "pos_receipt_number",
            "transaction_amount",
        ]


class StampCycleSerializer(serializers.ModelSerializer):
    stamps = StampSerializer(many=True, read_only=True)

    class Meta:
        model = StampCycle
        fields = ["id", "cycle_number", "is_closed", "stamps"]


class MembershipSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(), source="customer", write_only=True
    )
    cycles = StampCycleSerializer(many=True, read_only=True)

    class Meta:
        model = Membership
        fields = [
            "id",
            "customer",
            "customer_id",
            "card_number",
            "start_date",
            "end_date",
            "status",
            "cycles",
        ]
        extra_kwargs = {
            "start_date": {"required": False},
            "end_date": {"required": False},
        }

    def create(self, validated_data):
        customer = validated_data.pop("customer")
        card_number = validated_data["card_number"]
        start_date = validated_data.get("start_date")
        end_date = validated_data.get("end_date")
        return Membership.create_new(
            customer=customer,
            card_number=card_number,
            start_date=start_date,
            end_date=end_date,
        )
