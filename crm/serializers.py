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
        settings = ProgramSettings.get_solo()
        start_date = validated_data.get("start_date") or timezone.localdate()
        end_date = validated_data.get("end_date") or start_date + timedelta(days=settings.membership_duration_months * 30)

        validated_data["start_date"] = start_date
        validated_data["end_date"] = end_date
        return super().create(validated_data)
