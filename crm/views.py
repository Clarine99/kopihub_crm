from rest_framework import viewsets

from .models import Membership
from .serializers import MembershipSerializer


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.select_related("customer").all()
    serializer_class = MembershipSerializer

    def perform_create(self, serializer):
        membership = serializer.save()
        membership.seed_welcome_reward()
