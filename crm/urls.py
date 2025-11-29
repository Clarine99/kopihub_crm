from rest_framework.routers import DefaultRouter

from .views import CustomerViewSet, MembershipViewSet, ProgramSettingsViewSet

router = DefaultRouter()
router.register(r"customers", CustomerViewSet, basename="customers")
router.register(r"memberships", MembershipViewSet, basename="memberships")
router.register(r"settings", ProgramSettingsViewSet, basename="settings")

urlpatterns = router.urls
