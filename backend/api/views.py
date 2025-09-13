from django.shortcuts import render
from rest_framework import viewsets, filters, status, permissions
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter, BooleanFilter, DateFilter
from django.db.models import Count, Sum, Q, F, Avg, OuterRef, Subquery, IntegerField, FloatField, Value, Case, When
from django.db.models.functions import Coalesce, ExtractDay, Now
from django.utils import timezone
from datetime import timedelta
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
import pandas as pd
import numpy as np
import math
import logging
from .models import Hospital, Supplier, MedicalSupply, InventoryBatch, SupplyRequest, RequestItem, InventoryAlert
from .serializers import (
    HospitalSerializer, SupplierSerializer, MedicalSupplySerializer,
    InventoryBatchSerializer, SupplyRequestSerializer, RequestItemSerializer,
    InventoryAlertSerializer, UserSerializer,
    RequestItemAllocationSerializer, HospitalBasicSerializer, MedicalSupplyBasicSerializer
)

logger = logging.getLogger(__name__)

# 令牌认证视图，扩展DRF自带的视图
class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        user_serializer = UserSerializer(user)
        return Response({
            'token': token.key,
            'user': user_serializer.data
        })

# 当前用户信息视图
class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

# 医院管理视图集
class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.filter(is_deleted=False)
    serializer_class = HospitalSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # 查询参数过滤
        name = self.request.query_params.get('name')
        region = self.request.query_params.get('region')
        level = self.request.query_params.get('level')
        
        if name:
            queryset = queryset.filter(name__icontains=name)
        if region:
            queryset = queryset.filter(region__icontains=region)
        if level:
            queryset = queryset.filter(level=level)
            
        return queryset

# 供应商管理视图集
class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.filter(is_deleted=False)
    serializer_class = SupplierSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # 查询参数过滤
        name = self.request.query_params.get('name')
        contact_person = self.request.query_params.get('contact_person')
        
        if name:
            queryset = queryset.filter(name__icontains=name)
        if contact_person:
            queryset = queryset.filter(contact_person__icontains=contact_person)
            
        return queryset

# 医疗物资视图集
class MedicalSupplyViewSet(viewsets.ModelViewSet):
    queryset = MedicalSupply.objects.filter(is_deleted=False)
    serializer_class = MedicalSupplySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_controlled']
    search_fields = ['name', 'description']
    template_name = None  # 避免DjangoFilter模板错误
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # 查询参数过滤
        name = self.request.query_params.get('name')
        category = self.request.query_params.get('category')
        is_controlled = self.request.query_params.get('is_controlled')
        
        if name:
            queryset = queryset.filter(name__icontains=name)
        if category:
            queryset = queryset.filter(category=category)
        if is_controlled is not None:
            is_controlled_bool = is_controlled.lower() == 'true'
            queryset = queryset.filter(is_controlled=is_controlled_bool)
            
        return queryset

# 库存批次视图集
class InventoryBatchViewSet(viewsets.ModelViewSet):
    queryset = InventoryBatch.objects.filter(is_deleted=False)
    serializer_class = InventoryBatchSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # 查询参数过滤
        hospital_id = self.request.query_params.get('hospital_id')
        supply_id = self.request.query_params.get('supply_id')
        expiring_soon = self.request.query_params.get('expiring_soon')
        
        if hospital_id:
            queryset = queryset.filter(hospital_id=hospital_id)
        if supply_id:
            queryset = queryset.filter(supply_id=supply_id)
        if expiring_soon:
            # 过滤30天内过期的物资
            thirty_days_later = timezone.now().date() + timedelta(days=30)
            queryset = queryset.filter(expiration_date__lte=thirty_days_later)
            
        return queryset

# 请求项目视图集
class RequestItemViewSet(viewsets.ModelViewSet):
    queryset = RequestItem.objects.filter(is_deleted=False)
    serializer_class = RequestItemSerializer

# 物资请求视图集
class SupplyRequestViewSet(viewsets.ModelViewSet):
    queryset = SupplyRequest.objects.filter(is_deleted=False).select_related('hospital', 'requester', 'approver')
    serializer_class = SupplyRequestSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # 查询参数过滤
        status = self.request.query_params.get('status')
        hospital_id = self.request.query_params.get('hospital_id')
        emergency = self.request.query_params.get('emergency')
        
        if status:
            queryset = queryset.filter(status=status)
        if hospital_id:
            queryset = queryset.filter(hospital_id=hospital_id)
        if emergency is not None:
            emergency_bool = emergency.lower() == 'true'
            queryset = queryset.filter(emergency=emergency_bool)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        request_obj = self.get_object()
        if request_obj.status != SupplyRequest.RequestStatus.SUBMITTED:
            return Response({"detail": "只能审批已提交状态的请求"}, status=status.HTTP_400_BAD_REQUEST)
            
        request_obj.status = SupplyRequest.RequestStatus.APPROVED
        request_obj.approver = request.user
        request_obj.approval_time = timezone.now()
        request_obj.save()
        
        return Response({"detail": "请求已批准"})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        request_obj = self.get_object()
        if request_obj.status != SupplyRequest.RequestStatus.SUBMITTED:
            return Response({"detail": "只能拒绝已提交状态的请求"}, status=status.HTTP_400_BAD_REQUEST)
            
        request_obj.status = SupplyRequest.RequestStatus.REJECTED
        request_obj.approver = request.user
        request_obj.approval_time = timezone.now()
        request_obj.save()
        
        return Response({"detail": "请求已拒绝"})
    
    @action(detail=True, methods=['post'], url_path='allocate-item')
    def allocate_item(self, request, pk=None):
        """
        Update the allocated quantity for a specific RequestItem within this SupplyRequest.
        Also triggers priority recalculation for requests of the same supply.
        Request body should contain 'item_id' and 'allocated_quantity'.
        """
        supply_request = self.get_object()
        item_id = request.data.get('item_id')
        allocated_quantity_str = request.data.get('allocated_quantity')
        allowed_statuses = [SupplyRequest.RequestStatus.APPROVED, SupplyRequest.RequestStatus.SUBMITTED]

        if not item_id or allocated_quantity_str is None:
            return Response(
                {"error": "请求体中缺少 'item_id' 或 'allocated_quantity'。"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            allocated_quantity = int(allocated_quantity_str)
        except (ValueError, TypeError):
            return Response(
                {"error": "'allocated_quantity' 必须是一个整数。"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            request_item = RequestItem.objects.select_related('supply').get(
                item_id=item_id, request=supply_request, is_deleted=False
            )
        except RequestItem.DoesNotExist:
            return Response(
                {"error": f"在此请求中未找到 ID 为 {item_id} 的请求项。"},
                status=status.HTTP_404_NOT_FOUND
            )

        if supply_request.status not in allowed_statuses:
            return Response(
                {"error": "只有状态为 '已批准' 或 '已提交' 的请求才能进行分配。"}, # 更新错误信息
                status=status.HTTP_400_BAD_REQUEST
            )

        if allocated_quantity < 0:
            return Response(
                {"error": "分配数量不能为负数。"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if allocated_quantity > request_item.quantity:
            return Response(
                {"error": f"分配数量 ({allocated_quantity}) 不能超过请求数量 ({request_item.quantity})。"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- 更新和保存 ---
        request_item.allocated = allocated_quantity
        request_item.save()

        # --- 触发优先级重新计算 ---
        supply_code = request_item.supply.unspsc_code
        if supply_code:
            try:
                calculate_and_update_priorities(supply_code)
            except Exception as e:
                logger.error(f"Error triggering priority recalculation: {e}")

        # 返回更新后的请求项数据
        serializer = RequestItemSerializer(request_item)
        return Response(serializer.data, status=status.HTTP_200_OK)

# 库存预警视图集
class InventoryAlertViewSet(viewsets.ModelViewSet):
    queryset = InventoryAlert.objects.filter(is_deleted=False)
    serializer_class = InventoryAlertSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # 查询参数过滤
        alert_type = self.request.query_params.get('alert_type')
        hospital_id = self.request.query_params.get('hospital_id')
        is_resolved = self.request.query_params.get('is_resolved')
        
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        if hospital_id:
            queryset = queryset.filter(hospital_id=hospital_id)
        if is_resolved is not None:
            is_resolved_bool = is_resolved.lower() == 'true'
            queryset = queryset.filter(is_resolved=is_resolved_bool)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        if alert.is_resolved:
            return Response({"detail": "预警已经解决"}, status=status.HTTP_400_BAD_REQUEST)
            
        alert.is_resolved = True
        alert.resolved_by = request.user
        alert.resolved_time = timezone.now()
        alert.save()
        
        return Response({"detail": "预警已标记为已解决"})

# 新增：用于物资分配的 RequestItem 视图集
class RequestItemAllocationFilter(FilterSet):
    supply_code = CharFilter(field_name='supply__unspsc_code', lookup_expr='exact')
    request__hospital_id = CharFilter(field_name='request__hospital_id', lookup_expr='exact')
    request__emergency = BooleanFilter(field_name='request__emergency')
    request__required_by__gte = DateFilter(field_name='request__required_by', lookup_expr='gte')
    request__required_by__lte = DateFilter(field_name='request__required_by', lookup_expr='lte')

    class Meta:
        model = RequestItem
        fields = [
            'supply_code',
            'request__hospital_id',
            'request__emergency',
            'request__required_by__gte',
            'request__required_by__lte',
        ]

class RequestItemAllocationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RequestItemAllocationSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RequestItemAllocationFilter
    # --- 修改排序字段 ---
    # 允许前端通过 'request.priority' (会被 OrderingFilter 理解为 request__priority) 进行排序
    # 以及其他需要的字段
    ordering_fields = ['request__priority', 'request__required_by', 'request__emergency']
    # 默认按 SupplyRequest 的优先级降序排序
    ordering = ['-request__priority']

    def get_queryset(self):
        supply_code = self.request.query_params.get('supply_code')
        if not supply_code:
            return RequestItem.objects.none()

        status_filter = Q(request__status=SupplyRequest.RequestStatus.APPROVED) | Q(request__status=SupplyRequest.RequestStatus.SUBMITTED)

        # 获取基础查询集
        queryset = RequestItem.objects.filter(
            status_filter,
            is_deleted=False,
            supply__unspsc_code=supply_code,
            quantity__gt=Coalesce(F('allocated'), 0)
        ).select_related(
            'supply',
            'request',
            'request__hospital'
        )

        # --- 让 OrderingFilter 处理排序 ---
        # 不需要在这里手动 .order_by(*self.ordering)
        # OrderingFilter 会根据请求参数和 ViewSet 的配置自动应用排序

        return queryset

# 数据大屏API
@api_view(['GET'])
def dashboard_supplies_overview(request):
    """物资类别总览 (优化版)"""
    try:
        # 1. 统计不同类别物资数量 (保持不变)
        by_category = []
        for category_choice in MedicalSupply.SupplyCategory.choices:
            category = category_choice[0]
            category_display = category_choice[1]
            count = MedicalSupply.objects.filter(category=category, is_deleted=False).count()
            by_category.append({
                'category': category,
                'category_display': category_display,
                'count': count
            })

        # 2. 统计受控物资数量 (保持不变)
        controlled_supplies = MedicalSupply.objects.filter(
            is_controlled=True, is_deleted=False).count()

        # 3. 统计物资总数 (保持不变)
        total_supplies = MedicalSupply.objects.filter(is_deleted=False).count()

        # 4. 高效计算低库存物资数量
        batch_quantity_subquery = InventoryBatch.objects.filter(
            supply=OuterRef('pk'),
            is_deleted=False
        ).values('supply').annotate(
            total_qty=Sum('quantity')
        ).values('total_qty')

        low_stock_supplies = MedicalSupply.objects.filter(is_deleted=False).annotate(
            current_stock=Coalesce(Subquery(batch_quantity_subquery, output_field=IntegerField()), 0)
        ).filter(
            current_stock__lt=F('min_stock_level')
        ).count()

        return Response({
            'by_category': by_category,
            'total_supplies': total_supplies,
            'controlled_supplies': controlled_supplies,
            'low_stock_supplies': low_stock_supplies
        })
    except Exception as e:
        import traceback
        logger.error("--- ERROR in dashboard_supplies_overview ---", exc_info=True)
        return Response(
            {"error": "服务器内部错误", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def dashboard_hospitals_overview(request):
    """医院资源概览"""
    try:
        by_level = []
        for level_choice in Hospital.HospitalLevel.choices:
            level = level_choice[0]
            level_display = level_choice[1]
            count = Hospital.objects.filter(level=level, is_deleted=False).count()
            by_level.append({
                'level': level,
                'level_display': level_display,
                'count': count
            })
        
        total_hospitals = Hospital.objects.filter(is_deleted=False).count()
        active_hospitals = Hospital.objects.filter(is_active=True, is_deleted=False).count()
        
        total_capacity = Hospital.objects.filter(is_deleted=False).aggregate(
            total=Sum('storage_volume'))['total'] or 0
        current_usage = Hospital.objects.filter(is_deleted=False).aggregate(
            used=Sum('current_capacity'))['used'] or 0
        
        return Response({
            'by_level': by_level,
            'total_hospitals': total_hospitals,
            'active_hospitals': active_hospitals,
            'total_capacity': total_capacity,
            'current_usage': current_usage
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def dashboard_inventory_alerts(request):
    """
    获取库存预警概览和最近预警列表 (用于左下角组件)。
    """
    try:
        total_alerts = InventoryAlert.objects.filter(is_deleted=False).count()

        unresolved_alerts = InventoryAlert.objects.filter(is_deleted=False, is_resolved=False).count()

        recent_alerts_qs = InventoryAlert.objects.filter(is_deleted=False) \
                                                .select_related('hospital', 'supply', 'batch') \
                                                .order_by('-created_at')[:5]

        serializer = InventoryAlertSerializer(recent_alerts_qs, many=True)
        recent_alerts_data = serializer.data

        data = {
            'total_alerts': total_alerts,
            'unresolved_alerts': unresolved_alerts,
            'recent_alerts': recent_alerts_data
        }
        return Response(data)

    except Exception as e:
        logger.error("--- ERROR in dashboard_inventory_alerts ---", exc_info=True)
        return Response(
            {"error": "服务器内部错误", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def wgs84_to_bd09(lon, lat):
    """
    WGS84坐标系转百度坐标系(BD09)
    :param lon: WGS84坐标系的经度
    :param lat: WGS84坐标系的纬度
    :return: 百度坐标系的经度, 纬度
    """
    def _transformlat(lon, lat):
        ret = -100.0 + 2.0 * lon + 3.0 * lat + 0.2 * lat * lat + \
              0.1 * lon * lat + 0.2 * math.sqrt(abs(lon))
        ret += (20.0 * math.sin(6.0 * lon * math.pi) + 20.0 *
                math.sin(2.0 * lon * math.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lat * math.pi) + 40.0 *
                math.sin(lat / 3.0 * math.pi)) * 2.0 / 3.0
        ret += (160.0 * math.sin(lat / 12.0 * math.pi) + 320 *
                math.sin(lat * math.pi / 30.0)) * 2.0 / 3.0
        return ret

    def _transformlon(lon, lat):
        ret = 300.0 + lon + 2.0 * lat + 0.1 * lon * lon + \
              0.1 * lon * lat + 0.1 * math.sqrt(abs(lon))
        ret += (20.0 * math.sin(6.0 * lon * math.pi) + 20.0 *
                math.sin(2.0 * lon * math.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lon * math.pi) + 40.0 *
                math.sin(lon / 3.0 * math.pi)) * 2.0 / 3.0
        ret += (150.0 * math.sin(lon / 12.0 * math.pi) + 300.0 *
                math.sin(lon / 30.0 * math.pi)) * 2.0 / 3.0
        return ret

    def wgs84_to_gcj02(lon, lat):
        a = 6378245.0
        ee = 0.00669342162296594323
        dlon = _transformlon(lon - 105.0, lat - 35.0)
        dlat = _transformlat(lon - 105.0, lat - 35.0)
        radlat = lat / 180.0 * math.pi
        magic = math.sin(radlat)
        magic = 1 - ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlon = (dlon * 180.0) / (a / sqrtmagic * math.cos(radlat) * math.pi)
        dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * math.pi)
        mglat = lat + dlat
        mglon = lon + dlon
        return mglon, mglat

    def gcj02_to_bd09(lon, lat):
        x_pi = math.pi * 3000.0 / 180.0
        z = math.sqrt(lon * lon + lat * lat) + 0.00002 * math.sin(lat * x_pi)
        theta = math.atan2(lat, lon) + 0.000003 * math.cos(lon * x_pi)
        bdlon = z * math.cos(theta) + 0.0065
        bdlat = z * math.sin(theta) + 0.006
        return bdlon, bdlat

    lon_gcj02, lat_gcj02 = wgs84_to_gcj02(lon, lat)
    lon_bd09, lat_bd09 = gcj02_to_bd09(lon_gcj02, lat_gcj02)
    
    return lon_bd09, lat_bd09

@api_view(['GET'])
def dashboard_hospitals_map(request):
    """医院分布地图"""
    try:
        hospitals = Hospital.objects.filter(is_deleted=False, is_active=True)
        
        map_data = []
        for hospital in hospitals:
            if hospital.geo_location:
                usage_ratio = 0
                if hospital.storage_volume > 0:
                    usage_ratio = (hospital.current_capacity / hospital.storage_volume) * 100
                
                alerts_count = InventoryAlert.objects.filter(
                    hospital=hospital, is_resolved=False, is_deleted=False
                ).count()
                
                status = "normal"
                if usage_ratio >= 90:
                    status = "danger"
                elif usage_ratio >= 70:
                    status = "warning"
                
                lon_wgs84 = hospital.geo_location.x
                lat_wgs84 = hospital.geo_location.y
                lon_bd09, lat_bd09 = wgs84_to_bd09(lon_wgs84, lat_wgs84)
                
                map_data.append({
                    'hospital_id': hospital.hospital_id,
                    'name': hospital.name,
                    'level_display': hospital.get_level_display(),
                    'region': hospital.region,
                    'geo_location': {
                        'type': 'Point',
                        'coordinates': [lon_bd09, lat_bd09]
                    },
                    'usage_ratio': usage_ratio,
                    'alerts_count': alerts_count,
                    'status': status,
                    'value': [lon_bd09, lat_bd09, {
                        'alerts_count': alerts_count,
                        'usage_ratio': usage_ratio
                    }]
                })
        
        return Response(map_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def dashboard_request_fulfillment(request):
    """物资请求履行计划 (使用 Serializer)"""
    try:
        pending_requests_qs = SupplyRequest.objects.filter(
            status=SupplyRequest.RequestStatus.SUBMITTED,
            is_deleted=False
        ).select_related('hospital', 'requester').order_by('-emergency', 'request_time')[:5]

        approved_requests_qs = SupplyRequest.objects.filter(
            status=SupplyRequest.RequestStatus.APPROVED,
            is_deleted=False
        ).select_related('hospital', 'approver', 'requester').order_by('-approval_time')[:5]

        fulfilled_requests_qs = SupplyRequest.objects.filter(
            status=SupplyRequest.RequestStatus.FULFILLED,
            is_deleted=False
        ).select_related('hospital', 'approver', 'requester').order_by('-updated_at')[:5]

        pending_serializer = SupplyRequestSerializer(pending_requests_qs, many=True)
        approved_serializer = SupplyRequestSerializer(approved_requests_qs, many=True)
        fulfilled_serializer = SupplyRequestSerializer(fulfilled_requests_qs, many=True)

        return Response({
            'pending_requests': pending_serializer.data,
            'approved_requests': approved_serializer.data,
            'fulfilled_requests': fulfilled_serializer.data
        })
    except Exception as e:
        logger.error("--- ERROR in dashboard_request_fulfillment ---", exc_info=True)
        return Response(
            {"error": "获取请求履行数据失败", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def dashboard_alert_trends(request):
    """预警趋势"""
    try:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        date_labels = []
        current_date = start_date
        while current_date <= end_date:
            date_labels.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        datasets = []
        for alert_type_choice in InventoryAlert.AlertType.choices:
            alert_type = alert_type_choice[0]
            alert_type_display = alert_type_choice[1]
            
            data = []
            for label_date in date_labels:
                date_obj = timezone.datetime.strptime(label_date, '%Y-%m-%d').date()
                count = InventoryAlert.objects.filter(
                    alert_type=alert_type,
                    created_at__date=date_obj,
                    is_deleted=False
                ).count()
                data.append(count)
            
            datasets.append({
                'type': alert_type,
                'type_display': alert_type_display,
                'data': data
            })
        
        return Response({
            'labels': date_labels,
            'datasets': datasets
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def dashboard_hospital_rankings(request):
    """医院库存状态排名"""
    try:
        hospitals = Hospital.objects.filter(is_deleted=False, is_active=True)
        
        rankings = []
        for hospital in hospitals:
            usage_ratio = 0
            if hospital.storage_volume > 0:
                usage_ratio = (hospital.current_capacity / hospital.storage_volume) * 100
            
            rankings.append({
                'hospital_id': hospital.hospital_id,
                'name': hospital.name,
                'level_display': hospital.get_level_display(),
                'region': hospital.region,
                'storage_volume': hospital.storage_volume,
                'current_capacity': hospital.current_capacity,
                'usage_ratio': usage_ratio
            })
        
        rankings.sort(key=lambda x: x['usage_ratio'], reverse=True)
        
        return Response(rankings[:10])
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def dashboard_request_status(request):
    """物资请求状态"""
    try:
        total_requests = SupplyRequest.objects.filter(is_deleted=False).count()
        
        emergency_requests = SupplyRequest.objects.filter(
            emergency=True, is_deleted=False).count()
        
        pending_approval = SupplyRequest.objects.filter(
            status=SupplyRequest.RequestStatus.SUBMITTED, is_deleted=False).count()
        
        by_status = []
        for status_choice in SupplyRequest.RequestStatus.choices:
            status = status_choice[0]
            status_display = status_choice[1]
            count = SupplyRequest.objects.filter(status=status, is_deleted=False).count()
            
            if count > 0:
                by_status.append({
                    'status': status,
                    'status_display': status_display,
                    'count': count
                })
        
        return Response({
            'total_requests': total_requests,
            'emergency_requests': emergency_requests,
            'pending_approval': pending_approval,
            'by_status': by_status
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

# --- 辅助函数：计算优先级 (严格按照 Solve2.py 逻辑) ---
def calculate_and_update_priorities(supply_code: str):
    """
    Calculates and updates the priority score for active SupplyRequests
    related to a specific medical supply using Entropy Weight + TOPSIS,
    strictly following the logic from Solve2.py.
    """
    try:
        # 1. 获取相关的、未完成的请求项
        relevant_items = RequestItem.objects.filter(
            supply__unspsc_code=supply_code,
            request__status__in=[SupplyRequest.RequestStatus.SUBMITTED, SupplyRequest.RequestStatus.APPROVED],
            is_deleted=False
        ).select_related(
            'request', 'request__hospital', 'supply'
        ).annotate(
            hospital_level_factor=Case(
                # ... (与之前相同的 Case When 语句) ...
                When(request__hospital__level=Hospital.HospitalLevel.THIRD_A, then=Value(1.0)),
                When(request__hospital__level=Hospital.HospitalLevel.THIRD_B, then=Value(0.9)),
                When(request__hospital__level=Hospital.HospitalLevel.SECOND_A, then=Value(0.8)),
                When(request__hospital__level=Hospital.HospitalLevel.SECOND_B, then=Value(0.7)),
                When(request__hospital__level=Hospital.HospitalLevel.FIRST_A, then=Value(0.6)),
                When(request__hospital__level=Hospital.HospitalLevel.FIRST_B, then=Value(0.5)),
                When(request__hospital__level=Hospital.HospitalLevel.DISTRICT, then=Value(0.4)),
                When(request__hospital__level=Hospital.HospitalLevel.COMMUNITY, then=Value(0.3)),
                When(request__hospital__level=Hospital.HospitalLevel.OTHER, then=Value(0.2)),
                default=Value(0.1),
                output_field=FloatField()
            ),
            requested_qty=F('quantity'),
            allocated_qty=Coalesce(F('allocated'), 0),
            # 获取物资的全局最小库存水平
            supply_min_stock=F('supply__min_stock_level')
        ).filter(
            requested_qty__gt=F('allocated_qty') # 只处理未完全分配的项
        )

        if not relevant_items.exists():
            logger.info(f"No relevant, unfulfilled items found for priority calculation for supply {supply_code}.")
            return

        # 2. 准备 DataFrame 数据
        data = []
        request_ids_to_update = set()
        today = timezone.now().date()

        for item in relevant_items:
            request_ids_to_update.add(item.request.request_id)
            hospital_id = item.request.hospital.hospital_id
            supply_code_for_inventory = item.supply.unspsc_code

            # --- 库存相关计算 ---
            valid_batches = InventoryBatch.objects.filter(
                hospital_id=hospital_id,
                supply__unspsc_code=supply_code_for_inventory,
                is_deleted=False,
                expiration_date__gte=today,
                quantity__gt=0
            )
            # total_quantity 对应 Solve2.py 中的 total_quantity
            current_stock = valid_batches.aggregate(total_qty=Coalesce(Sum('quantity'), 0))['total_qty']

            weighted_days_sum = 0
            total_qty_for_avg = 0
            for batch in valid_batches:
                days_remaining = (batch.expiration_date - today).days
                days = max(0, days_remaining)
                weighted_days_sum += days * batch.quantity
                total_qty_for_avg += batch.quantity

            # avg_days_remaining (成本指标)
            avg_days_remaining = (weighted_days_sum / total_qty_for_avg) if total_qty_for_avg > 0 else 0
            # --- 库存相关计算结束 ---

            requested = item.requested_qty
            allocated = item.allocated_qty
            needed_qty = requested - allocated # 确保 needed_qty > 0

            # --- 计算 Solve2.py 中的指标 ---
            # stock_gap (效益指标)
            stock_gap = needed_qty - current_stock

            # ratio_shortage (效益指标)
            min_stock = item.supply_min_stock if item.supply_min_stock is not None else 0
            ratio_shortage = 0.0 # 默认值
            if needed_qty > 0: # 避免除以零
                numerator = current_stock + needed_qty - min_stock
                ratio_shortage = numerator / needed_qty
            else:
                # 如果 needed_qty 为 0 或负数，这个比率没有明确意义，可以设为0或根据业务逻辑处理
                ratio_shortage = 0.0 # 或者 1.0? 需要确认逻辑

            data.append({
                'request_id': item.request.request_id,
                'item_id': item.item_id,
                'hospital_name': item.request.hospital.name, # 仅用于调试
                # --- 使用 Solve2.py 定义的指标 ---
                'level': item.hospital_level_factor, # 效益
                'stock_gap': stock_gap,              # 效益 (按 Solve2.py)
                'ratio_shortage': ratio_shortage,    # 效益 (按 Solve2.py)
                'avg_days_remaining': avg_days_remaining, # 成本
            })

        if not data:
            logger.warning(f"No data generated for DataFrame for supply {supply_code}.")
            return

        df = pd.DataFrame(data)
        logger.debug(f"\n--- Debugging for supply: {supply_code} (Solve2.py logic) ---")
        logger.debug("Raw Data DataFrame (first 5 rows):\n" + df.head().to_string())

        if len(df) <= 1:
            logger.info(f"Only one or zero items for supply {supply_code}, setting priority to 0.5 or skipping.")
            if len(df) == 1:
                 RequestItem.objects.filter(pk=df.iloc[0]['item_id']).update(priority=0.5)
                 SupplyRequest.objects.filter(pk=df.iloc[0]['request_id']).update(priority=0.5)
            return

        # --- 3. 定义效益和成本指标 (严格按照 Solve2.py) ---
        benefit_cols = ['level', 'stock_gap', 'ratio_shortage']
        cost_cols    = ['avg_days_remaining']
        all_cols = benefit_cols + cost_cols

        # --- 4. 规范化 (Min-Max) ---
        norm = pd.DataFrame(index=df.index)
        valid_cols_for_norm = [] # 用于熵权计算的列

        for col in all_cols:
            if col not in df.columns:
                logger.warning(f"Column '{col}' not found in DataFrame. Skipping.")
                continue

            # 填充 NaN (可以选择 0 或均值/中位数)
            df[col] = df[col].fillna(0)

            mn, mx = df[col].min(), df[col].max()

            if mx == mn:
                # 如果所有值都一样，无法进行有效归一化，熵权也会是0
                norm[col] = 0.5 # 或 0.0，取决于如何处理无差异指标
                logger.warning(f"Column '{col}' has no variance. Normalized to 0.5. Excluded from entropy weights.")
            else:
                valid_cols_for_norm.append(col) # 只有有差异的列参与熵权计算
                if col in benefit_cols:
                    norm[col] = (df[col] - mn) / (mx - mn)
                elif col in cost_cols:
                    norm[col] = (mx - df[col]) / (mx - mn)

            # 处理可能的 inf/-inf (虽然理论上不应出现)
            norm[col] = norm[col].replace([np.inf, -np.inf], np.nan).fillna(0.5)

        logger.debug("\nNormalized DataFrame (first 5 rows):\n" + norm.head().to_string())

        if not valid_cols_for_norm:
             logger.error(f"Error: No valid columns with variance available for normalization for supply {supply_code}. Cannot calculate priorities.")
             RequestItem.objects.filter(pk__in=list(df['item_id'])).update(priority=0.0)
             SupplyRequest.objects.filter(pk__in=list(request_ids_to_update)).update(priority=0.0)
             return

        # --- 5. 熵权计算 ---
        # 只对有方差的列计算熵权
        norm_for_entropy = norm[valid_cols_for_norm] + 1e-12 # 避免 log(0)

        P = norm_for_entropy.div(norm_for_entropy.sum(axis=0), axis=1)
        E_log_part = P * np.log(P)
        # 确保分母不为0
        log_len_df = np.log(len(df)) if len(df) > 1 else 1.0
        if log_len_df == 0: log_len_df = 1.0 # 防止 len(df)=1 时 log(1)=0

        E = - E_log_part.sum(axis=0) / log_len_df
        E = np.clip(E, 0, 1) # 确保熵在 [0, 1]
        d = 1 - E # 差异度
        W_sum = d.sum()

        W = pd.Series(dtype=float)
        if W_sum == 0 or pd.isna(W_sum) or W_sum < 1e-9:
             logger.warning(f"Entropy weights sum is zero or NaN for supply {supply_code}. Assigning equal weights to valid columns.")
             num_valid_cols = len(valid_cols_for_norm)
             equal_weight = 1.0 / num_valid_cols if num_valid_cols > 0 else 0
             W = pd.Series([equal_weight] * num_valid_cols, index=valid_cols_for_norm)
        else:
             W = d / W_sum

        logger.debug("\nCalculated Entropy Weights:\n" + W.to_string())

        # --- 6. TOPSIS 排序 ---
        # 使用所有归一化列进行加权，权重来自熵权计算结果，无权重的列权重为0
        V = pd.DataFrame(index=norm.index)
        for col in norm.columns:
            weight = W.get(col, 0.0) # 获取权重，默认为0
            V[col] = norm[col] * weight

        V = V.fillna(0.0)
        logger.debug("\nWeighted Normalized DataFrame (first 5 rows):\n" + V.head().to_string())

        v_plus  = V.max()
        v_minus = V.min()
        S_plus  = np.sqrt(((V - v_plus)**2).sum(axis=1))
        S_minus = np.sqrt(((V - v_minus)**2).sum(axis=1))
        S_sum = S_plus + S_minus
        df['priority_score'] = np.where(S_sum < 1e-9, 0.5, S_minus / S_sum)

        # 打印调试信息
        temp_df = pd.DataFrame({
            'item_id': df['item_id'],
            'S_plus': S_plus, 'S_minus': S_minus, 'S_sum': S_sum,
            'priority_score': df['priority_score']
        })
        logger.debug("\nDistances and Final Scores (first 5 rows):\n" + temp_df.head().to_string())
        logger.debug("--- End Debugging ---")

        # --- 7. 更新数据库 ---
        item_updates = []
        for index, row in df.iterrows():
            item_id = row['item_id']
            priority_score = row['priority_score']
            score = max(0.0, min(1.0, priority_score))
            if pd.isna(score):
                logger.warning(f"Calculated priority for item {item_id} is NaN. Setting to 0.")
                score = 0.0
            item_updates.append(RequestItem(pk=item_id, priority=score))

        if item_updates:
            RequestItem.objects.bulk_update(item_updates, ['priority'])
            logger.info(f"Successfully updated priorities for {len(item_updates)} request items for supply {supply_code}.")

        # 更新 SupplyRequest 的 priority (取相关 items 的最大值)
        final_priorities = df.groupby('request_id')['priority_score'].max()
        request_updates = []
        for request_id, priority_score in final_priorities.items():
            score = max(0.0, min(1.0, priority_score))
            if pd.isna(score):
                logger.warning(f"Calculated priority for request {request_id} is NaN. Setting to 0.")
                score = 0.0
            request_updates.append(SupplyRequest(pk=request_id, priority=score))

        if request_updates:
            SupplyRequest.objects.bulk_update(request_updates, ['priority'])
            logger.info(f"Successfully updated priorities for {len(request_updates)} requests related to supply {supply_code}.")

    except Exception as e:
        logger.error(f"Error calculating priorities for supply {supply_code}: {e}", exc_info=True)
