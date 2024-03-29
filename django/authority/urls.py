from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import routers
import authority.views
import entity.views

router = routers.DefaultRouter()

urlpatterns = [
    path("", authority.views.HomeView.as_view(), name="home"),
    path("api/", include(router.urls)),
    path("person/<int:pk>/populate_viaf/", entity.views.PopulateVIAF.as_view(), name="person-populate-viaf"),
    path("person/<int:pk>/populate_lcnaf/", entity.views.PopulateLCNAF.as_view(), name="person-populate-lcnaf"),
    path(
        "reconcile/",
        authority.views.ReconciliationEndpoint.as_view(),
        name="reconciliation_endpoint",
    ),
    path(
        "reconcile/extend/",
        authority.views.DataExtensionEndpoint.as_view(),
        name="reconcile-extend",
    ),
    path(
        "reconcile/suggest/",
        authority.views.SuggestEndpoint.as_view(),
        name="reconcile-suggest",
    ),
    path(
        "reconcile/suggest/flyout/<int:pk>/",
        entity.views.FlyoutView.as_view(),
        name="flyout",
    ),
    path(
        "reconcile/preview/<int:pk>/",
        entity.views.PreviewView.as_view(),
        name="preview",
    ),
    path(
        "current_user/",
        authority.views.CurrentUserView.as_view(),
        name="current_user",
    ),
    path("auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("silk/", include("silk.urls", namespace="silk")),
]
