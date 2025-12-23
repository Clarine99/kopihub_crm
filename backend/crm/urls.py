from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomerViewSet,
    MembershipCardViewSet,
    MembershipViewSet,
    ProgramSettingsViewSet,
    RewardReportView,
    SummaryReportView,
    TransactionReportView,
)

router = DefaultRouter()
router.register(r"customers", CustomerViewSet, basename="customers")
router.register(r"memberships", MembershipViewSet, basename="memberships")
router.register(r"cards", MembershipCardViewSet, basename="cards")
router.register(r"settings", ProgramSettingsViewSet, basename="settings")

urlpatterns = [
    *router.urls,
    path("reports/summary/", SummaryReportView.as_view(), name="reports-summary"),
    path("reports/rewards/", RewardReportView.as_view(), name="reports-rewards"),
    path("reports/transactions/", TransactionReportView.as_view(), name="reports-transactions"),
]
