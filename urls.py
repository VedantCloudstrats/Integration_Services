from django.urls import path
from .views import IntegrationStatusView, CMMSSyncView

urlpatterns = [
    path("sync/status/", IntegrationStatusView.as_view(), name="status"),
    path("sync/", CMMSSyncView.as_view(), name="sync"),
]
