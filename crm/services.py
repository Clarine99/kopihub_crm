from decimal import Decimal

from django.db import transaction

from .models import (
    Membership,
    ProgramSettings,
    RewardType,
    Stamp,
    StampCycle,
)


def get_or_create_active_cycle(membership: Membership) -> StampCycle:
    cycles = membership.cycles.order_by("cycle_number")
    active_cycle = cycles.filter(is_closed=False).last()
    if active_cycle is None:
        next_number = (cycles.last().cycle_number + 1) if cycles.exists() else 1
        active_cycle = StampCycle.objects.create(
            membership=membership,
            cycle_number=next_number,
            is_closed=False,
        )
    return active_cycle


@transaction.atomic
def award_stamp_for_transaction(
    membership: Membership,
    transaction_amount: Decimal,
    pos_receipt_number: str | None = None,
) -> Stamp | None:
    settings = ProgramSettings.get_solo()
    membership.refresh_status_by_date()

    if not membership.is_active:
        return None

    if transaction_amount < Decimal(settings.min_amount_for_stamp):
        return None

    cycle = get_or_create_active_cycle(membership)
    next_number = cycle.stamp_count + 1
    if next_number > 10:
        cycle.is_closed = True
        cycle.save(update_fields=["is_closed"])
        cycle = get_or_create_active_cycle(membership)
        next_number = 1

    reward_type = RewardType.NONE
    if next_number == 1:
        reward_type = settings.reward_stamp_1_type
    elif next_number == 10:
        reward_type = settings.reward_stamp_10_type

    stamp = Stamp.objects.create(
        cycle=cycle,
        number=next_number,
        reward_type=reward_type,
        pos_receipt_number=pos_receipt_number,
        transaction_amount=transaction_amount,
    )

    if next_number == 10:
        cycle.is_closed = True
        cycle.save(update_fields=["is_closed"])

    return stamp


@transaction.atomic
def seed_initial_cycle(membership: Membership) -> None:
    settings = ProgramSettings.get_solo()
    cycle = StampCycle.objects.create(
        membership=membership,
        cycle_number=1,
        is_closed=False,
    )
    Stamp.objects.create(
        cycle=cycle,
        number=1,
        reward_type=settings.reward_stamp_1_type,
    )


@transaction.atomic
def redeem_reward_stamp(membership: Membership, reward_type: str) -> Stamp | None:
    stamp = (
        Stamp.objects.filter(
            cycle__membership=membership,
            reward_type=reward_type,
            redeemed_at__isnull=True,
        )
        .order_by("cycle__cycle_number", "number")
        .first()
    )
    if stamp:
        stamp.mark_redeemed()
    return stamp
