# KopiHub CRM Web App (Django + Next.js + PostgreSQL)

Dokumen ini merancang web app loyalty & membership Kopi Hub dengan tech stack:

- **Backend**: Django + Django REST Framework (API)
- **Frontend**: Next.js (App Router) + React
- **Database**: PostgreSQL

Fokus: implementasi program membership + stamp sesuai spesifikasi yang kamu tulis.

---

## 1. Arsitektur & High-Level Design

### 1.1. Komponen

1. **Django API**
   - Menyimpan semua data: Customer, Membership, StampCycle, Stamp, Reward, Settings, User (Kasir/Admin).
   - Menyediakan REST API (JSON) untuk diakses aplikasi Next.js.

2. **Next.js Frontend**
   - Role-based UI:
     - **Kasir**: registrasi member, cek member, tambah stamp, redeem reward.
     - **Admin/Owner**: kelola rules, monitoring member, reporting.
   - Autentikasi via JWT atau cookie session dari Django.

3. **PostgreSQL**
   - Satu database shared untuk Django.

4. **Integrasi POS (ESB)**
   - Tahap awal: hanya input manual `no_struk` dan `total_transaksi`.
   - Tahap lanjut: bisa integrasi via API ESB jika tersedia.

---

## 2. Struktur Project

### 2.1. Backend (Django)

Direktori contoh:

```bash
django_backend/
├── manage.py
├── config/              # settings, urls, wsgi/asgi
├── core/                # utilities, base models
├── crm/                 # app utama (customer, membership, stamp)
├── users/               # user & role kasir/admin
└── requirements.txt
```

Aktifkan apps:

```python
# config/settings.py
INSTALLED_APPS = [
    # bawaan django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # pihak ketiga
    "rest_framework",
    "rest_framework_simplejwt",  # kalau pakai JWT
    # apps internal
    "users",
    "crm",
]
```

### 2.2. Frontend (Next.js)

Direktori contoh (Next.js 14+ App Router):

```bash
next_frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                     # dashboard sederhana / landing
│   ├── login/
│   │   └── page.tsx
│   ├── cashier/
│   │   ├── members/
│   │   │   ├── new/
│   │   │   │   └── page.tsx         # registrasi member
│   │   │   └── [identifier]/
│   │   │       └── page.tsx         # detail member by card_number / phone
│   │   ├── add-stamp/
│   │   │   └── page.tsx             # form tambah stamp
│   │   └── redeem/
│   │       └── page.tsx             # pilih reward untuk redeem
│   └── admin/
│       ├── members/
│       │   └── page.tsx             # listing member
│       ├── settings/
│       │   └── page.tsx             # atur rule global
│       └── reports/
│           └── page.tsx             # reporting sederhana
├── lib/
│   └── api.ts                       # helper fetch ke Django
├── components/
│   ├── MemberSearchForm.tsx
│   ├── MemberSummaryCard.tsx
│   └── RewardList.tsx
└── package.json
```

---

## 3. Desain Database & Model Django (crm/models.py)

### 3.1. Model Customer

```python
# crm/models.py
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Customer(TimeStampedModel):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"
```

### 3.2. Model MembershipCard

Kartu fisik direpresentasikan sebagai entitas terpisah agar bisa dibuat lebih dulu lalu di-assign ke member.

```python
class MembershipCard(TimeStampedModel):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    card_number = models.CharField(max_length=50, unique=True)
    is_assigned = models.BooleanField(default=False)
    membership = models.OneToOneField(
        "Membership",
        on_delete=models.SET_NULL,
        related_name="card",
        null=True,
        blank=True,
    )

    @staticmethod
    def generate_card_number() -> str:
        return f"CARD-{uuid.uuid4().hex[:10].upper()}"

    def save(self, *args, **kwargs):
        if not self.card_number:
            self.card_number = self.generate_card_number()
            while type(self).objects.filter(card_number=self.card_number).exists():
                self.card_number = self.generate_card_number()
        super().save(*args, **kwargs)
```

### 3.3. Model Membership

```python
from datetime import timedelta


class MembershipStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    BLOCKED = "blocked", "Blocked"


class Membership(TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="memberships")
    card_number = models.CharField(max_length=50, unique=True, editable=False)

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=MembershipStatus.choices,
        default=MembershipStatus.ACTIVE,
    )

    def __str__(self):
        return f"{self.card_number} - {self.customer.name}"

    @property
    def is_active(self) -> bool:
        today = timezone.localdate()
        return self.status == MembershipStatus.ACTIVE and self.start_date <= today <= self.end_date

    def refresh_status_by_date(self):
        today = timezone.localdate()
        if self.status == MembershipStatus.BLOCKED:
            return
        if today > self.end_date:
            self.status = MembershipStatus.EXPIRED
            self.save(update_fields=["status"])

    @classmethod
    def create_new(
        cls,
        customer: Customer,
        card: MembershipCard,
        duration_months: int | None = None,
        start_date=None,
        end_date=None,
    ):
        settings = ProgramSettings.get_solo()
        months = duration_months or settings.membership_duration_months
        start = start_date or timezone.localdate()
        computed_end = end_date or (start + timedelta(days=months * 30))

        with transaction.atomic():
            membership = cls.objects.create(
                customer=customer,
                card_number=card.card_number,
                start_date=start,
                end_date=computed_end,
                status=MembershipStatus.ACTIVE,
            )
            card.membership = membership
            card.is_assigned = True
            card.save(update_fields=["membership", "is_assigned"])
            cycle = StampCycle.objects.create(
                membership=membership,
                cycle_number=1,
                is_closed=False,
            )
            Stamp.objects.create(
                cycle=cycle,
                number=1,
                reward_type=settings.reward_stamp_1_type or RewardType.FREE_DRINK,
            )
            return membership
```

### 3.4. Model StampCycle & Stamp

```python
class StampCycle(TimeStampedModel):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="cycles")
    cycle_number = models.PositiveIntegerField()  # 1,2,3,...
    is_closed = models.BooleanField(default=False)  # closed saat mencapai stamp #10

    class Meta:
        unique_together = ("membership", "cycle_number")

    def __str__(self):
        return f"{self.membership.card_number} - Cycle {self.cycle_number}"

    @property
    def stamp_count(self) -> int:
        return self.stamps.count()

    @property
    def is_full(self) -> bool:
        return self.stamp_count >= 10


class RewardType(models.TextChoices):
    NONE = "none", "No Reward"
    FREE_DRINK = "free_drink", "Free Americano/Latte"
    VOUCHER_50K = "voucher_50k", "Voucher Rp 50.000"


class Stamp(TimeStampedModel):
    cycle = models.ForeignKey(StampCycle, on_delete=models.CASCADE, related_name="stamps")
    number = models.PositiveIntegerField()  # 1..10

    reward_type = models.CharField(
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.NONE,
    )
    redeemed_at = models.DateTimeField(blank=True, null=True)

    pos_receipt_number = models.CharField(max_length=100, blank=True, null=True)
    transaction_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    class Meta:
        unique_together = ("cycle", "number")

    def __str__(self):
        return f"Stamp {self.number} - {self.cycle}"

    @property
    def is_redeemed(self) -> bool:
        return self.redeemed_at is not None

    def mark_redeemed(self):
        if not self.is_redeemed:
            self.redeemed_at = timezone.now()
            self.save(update_fields=["redeemed_at"])
```

### 3.5. Global Settings (rule program)

```python
class ProgramSettings(TimeStampedModel):
    # Single row (bisa pakai constraint nanti)
    is_active = models.BooleanField(default=True)

    membership_fee = models.PositiveIntegerField(default=25000)  # Rp 25.000
    membership_duration_months = models.PositiveIntegerField(default=3)

    discount_percent = models.PositiveIntegerField(default=10)  # 10%
    min_amount_for_stamp = models.PositiveIntegerField(default=50000)  # Rp 50.000

    reward_stamp_1_type = models.CharField(
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.FREE_DRINK,
    )
    reward_stamp_10_type = models.CharField(
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.VOUCHER_50K,
    )

    def __str__(self):
        return "Program Settings"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj
```

### 3.6. Helper: Award Stamp

Bisa taruh di `crm/services.py` atau method helper di model.

```python
# crm/services.py
from decimal import Decimal
from django.db import transaction


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
        # close cycle & create new, then gunakan cycle baru
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
```

> Catatan: saat registrasi member baru, kita buat **StampCycle #1 + Stamp #1 free drink** tanpa syarat transaksi.

---

## 4. Autentikasi & Role Kasir/Admin (users app)

### 4.1. Model User & Role

Pakai default `User` Django + extra field role.

```python
# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    CASHIER = "cashier", "Cashier"
    ADMIN = "admin", "Admin"


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CASHIER,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
```

Lalu di settings:

```python
AUTH_USER_MODEL = "users.User"
```

### 4.2. Permissions

- Kasir: boleh create membership, tambah stamp, redeem reward, lihat detail member.
- Admin: semua yang kasir bisa + kelola settings, block/unblock membership, reporting.

Implementasi bisa pakai custom permission di DRF atau pengecekan role manual di view.

---

## 5. API Design (Django REST Framework)

### 5.1. Serializers

```python
# crm/serializers.py
from rest_framework import serializers
from .models import Customer, Membership, StampCycle, Stamp, ProgramSettings


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
        fields = [
            "id",
            "cycle_number",
            "is_closed",
            "stamps",
        ]


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
```

### 5.2. Endpoint Utama

Contoh `crm/views.py` (DRF ViewSet + custom action):

```python
# crm/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Customer, Membership, Stamp, ProgramSettings
from .serializers import (
    CustomerSerializer,
    MembershipSerializer,
    StampSerializer,
)
from .services import award_stamp_for_transaction
from .models import MembershipStatus, RewardType


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.select_related("customer").all()
    serializer_class = MembershipSerializer
    permission_classes = [IsCashierOrAdminRole]

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Direct membership creation disabled. Use activate-card."},
            status=status.HTTP_403_FORBIDDEN,
        )

    @action(detail=False, methods=["get"], url_path="lookup")
    def lookup(self, request):
        """Cari membership by card_number atau phone."""
        identifier = request.query_params.get("q")
        if not identifier:
            return Response({"detail": "q is required"}, status=400)

        membership = (
            Membership.objects.select_related("customer")
            .filter(card_number__iexact=identifier)
            .first()
        )
        if membership is None:
            # coba cari by phone
            membership = (
                Membership.objects.select_related("customer")
                .filter(customer__phone__iexact=identifier)
                .order_by("-start_date")
                .first()
            )
        if membership is None:
            return Response({"detail": "Membership not found"}, status=404)

        membership.refresh_status_by_date()
        serializer = self.get_serializer(membership)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="activate-card")
    def activate_card(self, request):
        card_number = request.data.get("card_number")
        public_id = request.data.get("public_id")
        name = request.data.get("name")
        phone = request.data.get("phone")
        email = request.data.get("email")

        if not (card_number or public_id):
            return Response({"detail": "card_number or public_id is required"}, status=400)
        if not (name and phone):
            return Response({"detail": "name and phone are required"}, status=400)

        card = None
        if card_number:
            card = MembershipCard.objects.filter(card_number=card_number).first()
        if card is None and public_id:
            card = MembershipCard.objects.filter(public_id=public_id).first()
        if card is None:
            return Response({"detail": "Card not found"}, status=404)
        if card.is_assigned or card.membership:
            return Response({"detail": "Card already assigned"}, status=400)

        customer, created = Customer.objects.get_or_create(
            phone=phone,
            defaults={"name": name, "email": email},
        )
        if not created:
            updated = False
            if name and not customer.name:
                customer.name = name
                updated = True
            if email and not customer.email:
                customer.email = email
                updated = True
            if updated:
                customer.save(update_fields=["name", "email"])

        membership = Membership.create_new(customer=customer, card=card)
        serializer = self.get_serializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="add-stamp")
    def add_stamp(self, request, pk=None):
        membership = self.get_object()
        amount = request.data.get("transaction_amount")
        receipt = request.data.get("pos_receipt_number")
        if amount is None:
            return Response({"detail": "transaction_amount required"}, status=400)

        from decimal import Decimal

        stamp = award_stamp_for_transaction(
            membership,
            transaction_amount=Decimal(str(amount)),
            pos_receipt_number=receipt,
        )
        if stamp is None:
            return Response({"detail": "No stamp awarded"}, status=200)
        return Response(StampSerializer(stamp).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="redeem")
    def redeem_reward(self, request, pk=None):
        membership = self.get_object()
        reward_type = request.data.get("reward_type")
        if reward_type not in [RewardType.FREE_DRINK, RewardType.VOUCHER_50K]:
            return Response({"detail": "Invalid reward_type"}, status=400)

        # cari stamp dengan reward_type & belum redeemed
        stamp = (
            Stamp.objects.filter(
                cycle__membership=membership,
                reward_type=reward_type,
                redeemed_at__isnull=True,
            )
            .order_by("cycle__cycle_number", "number")
            .first()
        )
        if not stamp:
            return Response({"detail": "No reward available"}, status=400)

        stamp.mark_redeemed()
        return Response(StampSerializer(stamp).data)


class ProgramSettingsViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUserRole]

    def list(self, request):
        settings = ProgramSettings.get_solo()
        data = {
            "membership_fee": settings.membership_fee,
            "membership_duration_months": settings.membership_duration_months,
            "discount_percent": settings.discount_percent,
            "min_amount_for_stamp": settings.min_amount_for_stamp,
            "reward_stamp_1_type": settings.reward_stamp_1_type,
            "reward_stamp_10_type": settings.reward_stamp_10_type,
        }
        return Response(data)

    def create(self, request):
        settings = ProgramSettings.get_solo()
        for field in [
            "membership_fee",
            "membership_duration_months",
            "discount_percent",
            "min_amount_for_stamp",
            "reward_stamp_1_type",
            "reward_stamp_10_type",
        ]:
            if field in request.data:
                setattr(settings, field, request.data[field])
        settings.save()
        return self.list(request)
```

### 5.3. Routing API

```python
# crm/urls.py
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, MembershipViewSet, ProgramSettingsViewSet

router = DefaultRouter()
router.register(r"customers", CustomerViewSet, basename="customers")
router.register(r"memberships", MembershipViewSet, basename="memberships")
router.register(r"cards", MembershipCardViewSet, basename="cards")
router.register(r"settings", ProgramSettingsViewSet, basename="settings")

urlpatterns = router.urls
```

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("crm.urls")),
    path("api/auth/", include("users.api_urls")),  # login/logout/jwt, dll
]
```

---

## 6. Frontend Next.js – Flow Kasir

### 6.1. Helper API Client (lib/api.ts)

```ts
// next_frontend/lib/api.ts
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

  const res = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    credentials: "include", // kalau pakai cookie session
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}`);
  }

  return res.json();
}
```

### 6.2. Halaman Registrasi Member Baru

```tsx
// app/cashier/members/new/page.tsx
"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

export default function NewMemberPage() {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      // 1) create new card (auto-generated)
      const card = await apiFetch("/cards/", {
        method: "POST",
        body: JSON.stringify({}),
      });

      // 2) activate card -> create membership
      const membership = await apiFetch("/memberships/activate-card/", {
        method: "POST",
        body: JSON.stringify({
          card_number: card.card_number,
          name,
          phone,
        }),
      });

      // 3) backend harus otomatis buat Cycle #1 + Stamp #1 free drink
      setMessage(`Membership berhasil dibuat untuk ${membership.customer.name}`);
    } catch (err: any) {
      setMessage(err.message ?? "Terjadi kesalahan");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-md mx-auto p-4">
      <h1 className="text-xl font-semibold mb-4">Daftar Member Baru</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium">Nama</label>
          <input
            className="border rounded w-full p-2"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Nomor HP</label>
          <input
            className="border rounded w-full p-2"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-black text-white px-4 py-2 rounded"
        >
          {loading ? "Menyimpan..." : "Daftarkan"}
        </button>
      </form>
      {message && <p className="mt-4 text-sm">{message}</p>}
    </div>
  );
}
```

> Backend perlu sedikit penyesuaian: ketika `Membership` dibuat, otomatis buat `StampCycle` #1 dan Stamp #1 free drink.

### 6.3. Halaman Cek Member (lookup by kartu / HP)

```tsx
// app/cashier/members/[identifier]/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";

interface Stamp {
  id: number;
  number: number;
  reward_type: string;
  redeemed_at: string | null;
}

interface Cycle {
  id: number;
  cycle_number: number;
  is_closed: boolean;
  stamps: Stamp[];
}

interface Membership {
  id: number;
  card_number: string;
  status: string;
  start_date: string;
  end_date: string;
  customer: {
    name: string;
    phone: string;
  };
  cycles: Cycle[];
}

export default function MemberDetailPage() {
  const params = useParams<{ identifier: string }>();
  const [data, setData] = useState<Membership | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const membership = await apiFetch<Membership>(
          `/memberships/lookup?q=${params.identifier}`
        );
        setData(membership);
      } catch (err: any) {
        setError(err.message ?? "Member tidak ditemukan");
      }
    }
    if (params.identifier) load();
  }, [params.identifier]);

  if (error) return <div className="p-4">Error: {error}</div>;
  if (!data) return <div className="p-4">Memuat...</div>;

  const latestCycle = data.cycles[data.cycles.length - 1];
  const stampCount = latestCycle?.stamps.length ?? 0;

  const rewards = data.cycles
    .flatMap((c) => c.stamps)
    .filter((s) => s.reward_type !== "none");

  return (
    <div className="max-w-xl mx-auto p-4 space-y-4">
      <div className="border rounded p-4">
        <h1 className="text-xl font-semibold mb-2">{data.customer.name}</h1>
        <p>No HP: {data.customer.phone}</p>
        <p>No Kartu: {data.card_number}</p>
        <p>Status: {data.status}</p>
        <p>
          Periode: {data.start_date} s/d {data.end_date}
        </p>
      </div>

      {latestCycle && (
        <div className="border rounded p-4">
          <h2 className="font-semibold mb-2">Cycle #{latestCycle.cycle_number}</h2>
          <p>Stamp: {stampCount}/10</p>
        </div>
      )}

      <div className="border rounded p-4">
        <h2 className="font-semibold mb-2">Reward Belum Dipakai</h2>
        <ul className="list-disc list-inside space-y-1">
          {rewards.map((s) => (
            <li key={s.id}>
              Stamp #{s.number} - {s.reward_type} -
              {s.redeemed_at ? " Sudah dipakai" : " Belum dipakai"}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
```

### 6.4. Form Tambah Stamp

```tsx
// app/cashier/add-stamp/page.tsx
"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

export default function AddStampPage() {
  const [identifier, setIdentifier] = useState("");
  const [amount, setAmount] = useState("");
  const [receipt, setReceipt] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);

    try {
      // 1) lookup membership
      const membership = await apiFetch<any>(`/memberships/lookup?q=${identifier}`);
      // 2) call add-stamp
      const stamp = await apiFetch<any>(
        `/memberships/${membership.id}/add-stamp/`,
        {
          method: "POST",
          body: JSON.stringify({
            transaction_amount: amount,
            pos_receipt_number: receipt,
          }),
        }
      );

      if (stamp.detail === "No stamp awarded") {
        setMessage("Transaksi < 50k, tidak dapat stamp");
      } else {
        setMessage(
          `Stamp #${stamp.number} ditambahkan. Reward: ${stamp.reward_type}`
        );
      }
    } catch (err: any) {
      setMessage(err.message ?? "Terjadi kesalahan");
    }
  }

  return (
    <div className="max-w-md mx-auto p-4">
      <h1 className="text-xl font-semibold mb-4">Tambah Stamp</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium">No Kartu / No HP</label>
          <input
            className="border rounded w-full p-2"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Nominal Transaksi (Rp)</label>
          <input
            type="number"
            className="border rounded w-full p-2"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium">No Struk POS</label>
          <input
            className="border rounded w-full p-2"
            value={receipt}
            onChange={(e) => setReceipt(e.target.value)}
          />
        </div>
        <button
          type="submit"
          className="bg-black text-white px-4 py-2 rounded"
        >
          Simpan
        </button>
      </form>
      {message && <p className="mt-4 text-sm">{message}</p>}
    </div>
  );
}
```

### 6.5. Halaman Redeem Reward

Konsep:

1. Kasir input no kartu / no HP.
2. Tampilkan list reward yang tersedia.
3. Kasir pilih reward → call `/memberships/{id}/redeem/` dengan `reward_type` sesuai.

(Implementasi mirip AddStampPage, hanya endpoint berbeda.)

---

## 7. Admin Features (Ringkas)

### 7.1. Kelola Settings

- Next.js: halaman `/admin/settings` → form baca & update `ProgramSettings` via API.
- Hanya role `admin` yang bisa akses (cek JWT / cookie + role di frontend & backend).

### 7.2. Manajemen Member

- List member: GET `/api/memberships/?status=active/expired/blocked` (tambahkan filter di viewset).
- Block/unblock: PATCH `/api/memberships/{id}/` dengan field `status`.

### 7.3. Monitoring Stamp & Reward

- Endpoint tambahan:
  - `GET /api/memberships/{id}/history/` → detail cycle & stamp.
  - `GET /api/reports/rewards/` → agregasi reward terpakai vs belum.

### 7.4. Reporting

Contoh endpoint:

```python
# crm/views_reports.py (atau di views.py)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db.models import Count, Q

from .models import Membership, Stamp


class SummaryReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_members = Membership.objects.filter(status=MembershipStatus.ACTIVE).count()
        expired_members = Membership.objects.filter(status=MembershipStatus.EXPIRED).count()

        free_drink_used = Stamp.objects.filter(
            reward_type=RewardType.FREE_DRINK,
            redeemed_at__isnull=False,
        ).count()
        voucher_used = Stamp.objects.filter(
            reward_type=RewardType.VOUCHER_50K,
            redeemed_at__isnull=False,
        ).count()

        return Response(
            {
                "active_members": active_members,
                "expired_members": expired_members,
                "free_drink_used": free_drink_used,
                "voucher_used": voucher_used,
            }
        )
```

---

## 8. Hook Registrasi Member: Auto Cycle & Stamp #1

Ubah `Membership.create_new` atau override `MembershipViewSet.perform_create` supaya saat membership dibuat, otomatis:

1. Buat `StampCycle` #1.
2. Buat `Stamp` #1 dengan `reward_type=FREE_DRINK` (mengacu ke ProgramSettings).

```python
# crm/views.py (lanjutan dari MembershipViewSet)

    def perform_create(self, serializer):
        membership = serializer.save()

        from .models import StampCycle, Stamp, RewardType
        from .models import ProgramSettings

        settings = ProgramSettings.get_solo()

        cycle = StampCycle.objects.create(
            membership=membership,
            cycle_number=1,
            is_closed=False,
        )

        Stamp.objects.create(
            cycle=cycle,
            number=1,
            reward_type=settings.reward_stamp_1_type or RewardType.FREE_DRINK,
        )
```

---

## 9. Next Steps Implementasi

1. **Setup Project**
   - Buat project Django + app `crm` & `users`.
   - Setup PostgreSQL connection di `settings.py`.
   - Install DRF & SimpleJWT (jika pakai JWT).

2. **Migration & Admin**
   - Jalankan migrasi, buat superuser.
   - Register model di admin untuk debugging cepat (Customer, Membership, StampCycle, Stamp, ProgramSettings).

3. **Autentikasi**
   - Implement login endpoint (JWT atau session) dan integrasi dengan Next.js.

4. **Implement semua endpoint minimal**
   - `customers`, `memberships` + aksi `lookup`, `add-stamp`, `redeem`, `settings`, `reports`.

5. **Build UI Kasir di Next.js**
   - Halaman login, registrasi member, lookup member, add stamp, redeem reward.

6. **Build UI Admin**
   - Setting program, list member, simple reports.

7. **Testing Flow Nyata** di Kopi Hub
   - Skenario: member baru, transaksi rutin, reward redeem, membership expired.

---

Dokumen ini sudah cukup untuk kamu jadikan blueprint implementasi full project Django + Next.js + PostgreSQL untuk program membership Kopi Hub.
class MembershipCardViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = MembershipCard.objects.all()
    serializer_class = MembershipCardSerializer
    permission_classes = [IsCashierOrAdminRole]
