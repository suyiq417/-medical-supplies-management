from rest_framework import serializers
from .models import Hospital, Supplier, MedicalSupply, InventoryBatch, SupplyRequest, RequestItem, InventoryAlert, User

# 用户序列化器 (已存在，确保包含 username)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # 确保 username 在字段列表中
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_staff']

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        # 确保 contact_info (JSONField) 能被正确序列化
        fields = '__all__' # 包含所有字段
    
# 医疗物资序列化器 - 添加 category_display
class MedicalSupplySerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    # 使用 source='get_xxx_display' 来获取 Choice 字段的可读名称
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    # 如果 MedicalSupply 模型中有 unit 字段，也确保它包含在内
    # unit = serializers.CharField(read_only=True) # 假设模型中有 unit 字段

    class Meta:
        model = MedicalSupply
        # 包含所有字段，以及我们添加的 category_display
        fields = '__all__'
        # 如果只想包含特定字段，可以这样写：
        # fields = ['unspsc_code', 'name', 'category', 'category_display', 'unit', 'description', ...]


# 基础库存批次序列化器 (用于嵌套在预警中，避免循环引用或过多数据)
class InventoryBatchBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryBatch
        fields = ['batch_id', 'batch_number'] # 只包含基础信息


# 请求项目序列化器 - 嵌套物资信息
class RequestItemSerializer(serializers.ModelSerializer):
    # 嵌套 MedicalSupplySerializer 以获取物资详情
    supply = MedicalSupplySerializer(read_only=True)

    class Meta:
        model = RequestItem
        fields = '__all__' # 包含所有字段及嵌套的 supply

# 物资请求序列化器 - 嵌套请求项目和申请人信息
class SupplyRequestSerializer(serializers.ModelSerializer):
    # 嵌套 RequestItemSerializer (已存在)，现在它会包含物资详情
    items = RequestItemSerializer(many=True, read_only=True)
    # 嵌套 UserSerializer 以获取申请人信息
    requester = UserSerializer(read_only=True)
    # 嵌套 UserSerializer 以获取审批人信息
    approver = UserSerializer(read_only=True)
    # 添加医院名称 (如果需要)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    # 添加状态的可读名称
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SupplyRequest
        fields = '__all__' # 包含所有字段及嵌套的 items 和 requester 和 approver

class HospitalBasicSerializer(serializers.ModelSerializer):
    # 添加等级的可读名称
    level_display = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = Hospital
        # 包含前端需要的字段: id, name, level_display, region, address
        fields = ['hospital_id', 'name', 'level_display', 'region', 'address']

# 物资基础序列化器 (如果尚未存在或需要调整)
class MedicalSupplyBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalSupply
        fields = ['unspsc_code', 'name', 'unit'] # 包含前端表格所需字段

# 新增：用于物资分配视图的序列化器
class RequestItemAllocationSerializer(serializers.ModelSerializer):
    supply = MedicalSupplyBasicSerializer(read_only=True)
    # 使用 SerializerMethodField 获取嵌套的请求信息
    request = serializers.SerializerMethodField()

    class Meta:
        model = RequestItem
        fields = [
            'item_id',
            'supply',
            'quantity',
            'allocated',
            'notes',
            'request', # 包含来自父请求的关键信息
        ]

    def get_request(self, obj):
        # 返回父 SupplyRequest 中的特定字段
        if obj.request:
            return {
                'request_id': obj.request.request_id,
                'hospital': HospitalBasicSerializer(obj.request.hospital).data if obj.request.hospital else None,
                'priority': obj.request.priority,
                'emergency': obj.request.emergency,
                'required_by': obj.request.required_by,
                'status': obj.request.status,
                'status_display': obj.request.get_status_display(),
            }
        return None

# 库存批次序列化器 - 嵌套物资信息
class InventoryBatchSerializer(serializers.ModelSerializer):
    # 嵌套 MedicalSupplySerializer 以获取物资详情
    supply = MedicalSupplySerializer(read_only=True)
    # 嵌套 HospitalBasicSerializer (已修改，包含 level_display)
    hospital = HospitalBasicSerializer(read_only=True)
    # 嵌套 SupplierSerializer
    supplier = SupplierSerializer(read_only=True)
    # 嵌套 UserSerializer
    received_by = UserSerializer(read_only=True)

    class Meta:
        model = InventoryBatch
        fields = '__all__' # 包含所有字段及嵌套的 supply, hospital, supplier, received_by


# 库存预警序列化器 - 嵌套物资和批次(基础)信息
class InventoryAlertSerializer(serializers.ModelSerializer):
    # 假设已有 HospitalBasicSerializer
    hospital = HospitalBasicSerializer(read_only=True)
    # 嵌套 MedicalSupplyBasicSerializer 以获取物资基础信息
    supply = MedicalSupplySerializer(read_only=True) # 现在这里会包含 unspsc_code 和 name
    # 嵌套基础的批次序列化器
    batch = InventoryBatchBasicSerializer(read_only=True)
    # 添加预警类型的可读名称
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)


    class Meta:
        model = InventoryAlert
        fields = [
            'alert_id', 'hospital', 'supply', 'batch', 'alert_type', 'alert_type_display',
            'message', 'created_at', 'is_resolved', # ... 其他需要的字段 ...
        ]

class HospitalSerializer(serializers.ModelSerializer):
    # 添加等级和地区的可读名称 (如果前端需要直接显示)
    level_display = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = Hospital
        fields = '__all__' # 包含 level_display


class DashboardSummarySerializer(serializers.Serializer):
    hospital_count = serializers.IntegerField()
    supplier_count = serializers.IntegerField()
    supply_count = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    low_stock_alerts = serializers.IntegerField()
    expiring_alerts = serializers.IntegerField()
