from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    HospitalViewSet, SupplierViewSet, MedicalSupplyViewSet,
    InventoryBatchViewSet, SupplyRequestViewSet, InventoryAlertViewSet,
    CustomAuthToken, CurrentUserView,RequestItemAllocationViewSet,
    dashboard_supplies_overview, dashboard_hospitals_overview, 
    dashboard_inventory_alerts, dashboard_hospitals_map,
    dashboard_request_fulfillment, dashboard_alert_trends,
    dashboard_hospital_rankings, dashboard_request_status
)

router = DefaultRouter()
router.register(r'hospitals', HospitalViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'supplies', MedicalSupplyViewSet)
router.register(r'inventory-batches', InventoryBatchViewSet)
router.register(r'supply-requests', SupplyRequestViewSet)
router.register(r'inventory-alerts', InventoryAlertViewSet)
router.register(r'allocation-items', RequestItemAllocationViewSet, basename='allocation-item')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', CustomAuthToken.as_view()),
    path('auth/user/', CurrentUserView.as_view()),
    
    # 数据大屏API
    path('dashboard/supplies-overview/', dashboard_supplies_overview),
    path('dashboard/hospitals-overview/', dashboard_hospitals_overview),
    path('dashboard/inventory-alerts/', dashboard_inventory_alerts),
    path('dashboard/hospitals-map/', dashboard_hospitals_map),
    path('dashboard/request-fulfillment/', dashboard_request_fulfillment),
    path('dashboard/alert-trends/', dashboard_alert_trends),
    path('dashboard/hospital-rankings/', dashboard_hospital_rankings),
    path('dashboard/request-status/', dashboard_request_status),
]
