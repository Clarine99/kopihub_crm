from rest_framework.throttling import SimpleRateThrottle


class BaseUserRateThrottle(SimpleRateThrottle):
    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class ScanRateThrottle(BaseUserRateThrottle):
    scope = "scan"


class QrRateThrottle(BaseUserRateThrottle):
    scope = "qr"


class ReportsRateThrottle(BaseUserRateThrottle):
    scope = "reports"
