from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from banking.views import BankAccountViewSet, InstallmentViewSet, LoanViewSet

router = DefaultRouter()
router.register("accounts", BankAccountViewSet, basename="accounts")
router.register("loans", LoanViewSet, basename="loans")
router.register("installments", InstallmentViewSet, basename="installments")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
