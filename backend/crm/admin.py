from django.contrib import admin

from .models import AuditLog, Customer, Membership, MembershipCard, ProgramSettings, Stamp, StampCycle


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "created_at")
    search_fields = ("name", "phone", "email")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("card_number", "customer", "status", "start_date", "end_date")
    search_fields = ("card_number", "customer__name", "customer__phone")
    list_filter = ("status",)


@admin.register(MembershipCard)
class MembershipCardAdmin(admin.ModelAdmin):
    list_display = ("card_number", "public_id", "is_assigned", "membership")
    search_fields = ("card_number", "public_id")
    list_filter = ("is_assigned",)


@admin.register(StampCycle)
class StampCycleAdmin(admin.ModelAdmin):
    list_display = ("membership", "cycle_number", "is_closed")
    list_filter = ("is_closed",)


@admin.register(Stamp)
class StampAdmin(admin.ModelAdmin):
    list_display = ("cycle", "number", "reward_type", "redeemed_at")
    list_filter = ("reward_type", "redeemed_at")


@admin.register(ProgramSettings)
class ProgramSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "membership_fee",
        "membership_duration_months",
        "discount_percent",
        "min_amount_for_stamp",
        "reward_stamp_1_type",
        "reward_stamp_10_type",
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "membership", "card", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("membership__card_number", "card__card_number", "user__username")
