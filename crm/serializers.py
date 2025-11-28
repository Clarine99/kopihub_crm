from rest_framework import serializers

from .models import Customer, Membership


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "email"]


class MembershipSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()

    class Meta:
        model = Membership
        fields = [
            "id",
            "customer",
            "card_number",
            "start_date",
            "end_date",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]

    def create(self, validated_data):
        customer_data = validated_data.pop("customer")
        customer, _ = Customer.objects.get_or_create(**customer_data)
        membership = Membership.objects.create(customer=customer, **validated_data)
        return membership
