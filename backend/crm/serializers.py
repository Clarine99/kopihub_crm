from datetime import timedelta

from rest_framework import serializers
from django.utils import timezone

from .models import Customer, Membership, MembershipCard, ProgramSettings, Stamp, StampCycle


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
            "card_number": {"read_only": True},
        }

    def create(self, validated_data):
        if "start_date" not in validated_data:
            validated_data["start_date"] = timezone.localdate()
        if "end_date" not in validated_data:
            months = ProgramSettings.get_solo().membership_duration_months
            validated_data["end_date"] = validated_data["start_date"] + timedelta(days=months * 30)
        return super().create(validated_data)


class MembershipCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipCard
        fields = ["public_id", "card_number", "is_assigned"]
        read_only_fields = ["public_id", "card_number", "is_assigned"]
