from rest_framework import serializers

from .models import Customer, Membership, Stamp, StampCycle


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
    duration_months = serializers.IntegerField(required=False, min_value=1, write_only=True)
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
            "duration_months",
            "cycles",
        ]
        extra_kwargs = {
            "start_date": {"required": False},
            "end_date": {"required": False},
        }

    def create(self, validated_data):
        duration_months = validated_data.pop("duration_months", None)
        return Membership.create_new(
            customer=validated_data["customer"],
            card_number=validated_data["card_number"],
            duration_months=duration_months,
            start_date=validated_data.get("start_date"),
            end_date=validated_data.get("end_date"),
        )
