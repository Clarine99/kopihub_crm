from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomerViewSet,
    MembershipCardViewSet,
    MembershipViewSet,
    ProgramSettingsViewSet,
    RewardReportView,
    RewardReportCsvView,
    SummaryReportView,
    SummaryReportCsvView,
    TransactionDailyReportView,
    TransactionPeriodReportView,
    TransactionReportCsvView,
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
    path("reports/summary/csv/", SummaryReportCsvView.as_view(), name="reports-summary-csv"),
    path("reports/rewards/", RewardReportView.as_view(), name="reports-rewards"),
    path("reports/rewards/csv/", RewardReportCsvView.as_view(), name="reports-rewards-csv"),
    path("reports/transactions/", TransactionReportView.as_view(), name="reports-transactions"),
    path(
        "reports/transactions/daily/",
        TransactionDailyReportView.as_view(),
        name="reports-transactions-daily",
    ),
    path(
        "reports/transactions/period/",
        TransactionPeriodReportView.as_view(),
        name="reports-transactions-period",
    ),
    path(
        "reports/transactions/csv/",
        TransactionReportCsvView.as_view(),
        name="reports-transactions-csv",
    ),
]
