from datetime import timedelta

from rest_framework import serializers
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
        read_only_fields = ["number", "reward_type", "redeemed_at"]


class StampCycleSerializer(serializers.ModelSerializer):
    stamps = StampSerializer(many=True, read_only=True)

    class Meta:
        model = StampCycle
        fields = ["id", "cycle_number", "is_closed", "stamps"]
        read_only_fields = ["cycle_number", "is_closed", "stamps"]


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
        read_only_fields = ["status", "start_date", "end_date", "cycles"]

    def create(self, validated_data):
        settings = ProgramSettings.get_solo()
        start_date = validated_data.get("start_date") or timezone.localdate()
        duration_days = settings.membership_duration_months * 30
        end_date = validated_data.get("end_date") or (
            start_date + timedelta(days=duration_days)
        )
        validated_data["start_date"] = start_date
        validated_data["end_date"] = end_date
        return super().create(validated_data)


class ProgramSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramSettings
        fields = [
            "membership_fee",
            "membership_duration_months",
            "discount_percent",
            "min_amount_for_stamp",
            "reward_stamp_1_type",
            "reward_stamp_10_type",
        ]
