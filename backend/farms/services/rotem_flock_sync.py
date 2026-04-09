"""
Upsert active Flock from Rotem-derived House fields (batch dates, age, bird count).
"""
from __future__ import annotations

from typing import Optional, Tuple

from django.contrib.auth import get_user_model
from django.db import transaction

from farms.models import Flock
from houses.models import House, HouseMonitoringSnapshot

User = get_user_model()

ROTEM_BATCH_PREFIX = "ROTEM"


def _infer_start_date(house: House):
    return house.batch_start_date or house.chicken_in_date


def _infer_age_days(house: House) -> Optional[int]:
    if house.current_age_days is not None and house.current_age_days >= 0:
        return int(house.current_age_days)
    cd = house.current_day
    if cd is not None and cd >= 0:
        return int(cd)
    return None


def _latest_bird_count(house: House) -> Optional[int]:
    snap = (
        HouseMonitoringSnapshot.objects.filter(house=house, bird_count__isnull=False)
        .order_by("-timestamp")
        .values_list("bird_count", flat=True)
        .first()
    )
    return int(snap) if snap is not None else None


def _rotem_batch_number(house: House) -> str:
    """Stable batch id per house for Rotem sync upserts."""
    return f"{ROTEM_BATCH_PREFIX}-H{house.house_number}"


def can_sync_flock_from_rotem(house: House) -> Tuple[bool, str]:
    farm = house.farm
    if not farm:
        return False, "House has no farm."
    if farm.integration_type != "rotem":
        return False, "Farm is not connected via Rotem integration."
    start = _infer_start_date(house)
    if not start:
        return False, "No batch start date on house; sync Rotem house data first or set batch/chicken-in date."
    age = _infer_age_days(house)
    if age is None:
        return False, "Could not determine flock age (day-old) from house; wait for Rotem monitoring sync."
    if age < 0:
        return False, "House reports no active flock (empty or invalid age)."
    return True, ""


@transaction.atomic
def upsert_active_flock_from_rotem(house: House, user: Optional[User] = None) -> Tuple[Flock, bool]:
    """
    Create or update the single active Rotem-synced flock for this house.
    Returns (flock, created).
    """
    ok, msg = can_sync_flock_from_rotem(house)
    if not ok:
        raise ValueError(msg)

    start = _infer_start_date(house)
    age = _infer_age_days(house)
    batch_number = _rotem_batch_number(house)
    birds = _latest_bird_count(house) or house.capacity or 1000

    expected_harvest = None
    if house.expected_harvest_date:
        expected_harvest = house.expected_harvest_date
    elif house.chicken_out_date:
        expected_harvest = house.chicken_out_date

    status = "growing"
    if age is not None:
        if age <= 1:
            status = "arrival"
        elif age >= 35:
            status = "production"

    def _unique_flock_code(base: str) -> str:
        code = base
        n = 0
        while Flock.objects.filter(flock_code=code).exists():
            n += 1
            code = f"{base}-{n}"
        return code

    flock_code = _unique_flock_code(f"{house.id}-{batch_number}-{start.strftime('%Y%m%d')}")

    flock, created = Flock.objects.get_or_create(
        house=house,
        batch_number=batch_number,
        defaults={
            "flock_code": flock_code,
            "arrival_date": start,
            "start_date": start,
            "expected_harvest_date": expected_harvest,
            "initial_chicken_count": birds,
            "current_chicken_count": birds,
            "status": status,
            "is_active": True,
            "supplier": "",
            "notes": "Synced from Rotem integration",
            "created_by": user if user and user.is_authenticated else None,
        },
    )

    if not created:
        new_code = f"{house.id}-{batch_number}-{start.strftime('%Y%m%d')}"
        if flock.flock_code != new_code:
            conflict = Flock.objects.filter(flock_code=new_code).exclude(pk=flock.pk).first()
            flock.flock_code = new_code if not conflict else _unique_flock_code(new_code)
        flock.arrival_date = start
        flock.start_date = start
        if expected_harvest:
            flock.expected_harvest_date = expected_harvest
        if birds:
            if not flock.current_chicken_count:
                flock.current_chicken_count = birds
            if not flock.initial_chicken_count:
                flock.initial_chicken_count = birds
        flock.status = status
        flock.is_active = True
        if "Updated from Rotem integration" not in (flock.notes or ""):
            flock.notes = (flock.notes or "").strip() + "\nUpdated from Rotem integration."
        flock.save()

    Flock.objects.filter(house=house, is_active=True).exclude(pk=flock.pk).update(is_active=False)

    return flock, created
