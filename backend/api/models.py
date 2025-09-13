import uuid
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

# 基础模型类，包含通用字段
class BaseModel(models.Model):
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    is_deleted = models.BooleanField("是否删除", default=False)
    
    class Meta:
        abstract = True

# 医院信息表
class Hospital(BaseModel):
    class HospitalLevel(models.IntegerChoices):
        THIRD_A = 9, '三甲医院'
        THIRD_B = 8, '三乙医院'
        SECOND_A = 7, '二甲医院'
        SECOND_B = 6, '二乙医院'
        FIRST_A = 5, '一甲医院'
        FIRST_B = 4, '一乙医院'
        DISTRICT = 3, '区级医院'
        COMMUNITY = 2, '社区医院'
        OTHER = 1, '其他'

    hospital_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org_code = models.CharField("机构编码", max_length=20, unique=True)
    name = models.CharField("医院名称", max_length=100)
    level = models.IntegerField("医院等级", choices=HospitalLevel.choices)
    address = models.TextField("详细地址")
    geo_location = gis_models.PointField("地理坐标")  # 需要安装GEOS库
    contact_info = models.JSONField("联系信息", default=dict)
    storage_volume = models.DecimalField("仓储容量", max_digits=10, decimal_places=2)
    current_capacity = models.DecimalField("当前库存", max_digits=10, decimal_places=2)
    region = models.CharField("所属地区", max_length=50, blank=True)
    is_active = models.BooleanField("是否活跃", default=True)
    warning_threshold = models.DecimalField("库存预警阈值", max_digits=5, decimal_places=2, default=20.00, help_text="百分比，例如20.00表示当库存低于容量的20%时预警")
    
    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['org_code'], name='org_code_idx'),
        ]
        verbose_name = "医疗机构"

# 供应商信息
class Supplier(BaseModel):
    supplier_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("供应商名称", max_length=100)
    contact_person = models.CharField("联系人", max_length=50)
    contact_info = models.JSONField("联系方式", default=dict)
    address = models.TextField("地址", blank=True)
    credit_rating = models.PositiveSmallIntegerField("信用评级", default=3, validators=[MinValueValidator(1)])
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "供应商"
        indexes = [
            models.Index(fields=['name'], name='supplier_name_idx'),
        ]

# 医疗物资表
class MedicalSupply(BaseModel):
    class SupplyCategory(models.TextChoices):
        DRUG = 'DG', '药品'
        DEVICE = 'DV', '医疗设备'
        PPE = 'PP', '防护装备'
        REAGENT = 'RT', '检测试剂'
        CONSUMABLE = 'CS', '一次性耗材'
        OTHER = 'OT', '其他'

    unspsc_code = models.CharField("UNSPSC编码", max_length=20, primary_key=True)
    name = models.CharField("物资名称", max_length=200)
    category = models.CharField("物资类型", max_length=2, choices=SupplyCategory.choices)
    unit = models.CharField("计量单位", max_length=10)
    standard = models.CharField("执行标准", max_length=100)
    shelf_life = models.PositiveIntegerField("保质期(月)")
    storage_temp = models.CharField("存储温度", max_length=20)
    is_controlled = models.BooleanField("受控物资", default=False)
    description = models.TextField("描述", blank=True)
    avg_price = models.DecimalField("平均价格", max_digits=10, decimal_places=2, null=True, blank=True)
    min_stock_level = models.PositiveIntegerField("最低库存量", default=0)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplies')
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    class Meta:
        verbose_name = "医疗物资"
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'category'],
                name='unique_supply'
            )
        ]

# 医疗物资库存批次表
class InventoryBatch(BaseModel):
    batch_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch_number = models.CharField("批次号", max_length=50, unique=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='batches')
    supply = models.ForeignKey(MedicalSupply, on_delete=models.PROTECT, related_name='inventory')
    quantity = models.PositiveIntegerField("库存数量")
    production_date = models.DateField("生产日期")
    expiration_date = models.DateField("失效日期")
    storage_condition = models.JSONField("存储条件", default=dict)
    received_date = models.DateField("入库日期", default=timezone.now)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='received_batches')
    unit_price = models.DecimalField("单价", max_digits=10, decimal_places=2, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='batches')
    quality_check_passed = models.BooleanField("质检通过", default=True)
    notes = models.TextField("备注", blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['expiration_date'], name='expiry_idx'),
            models.Index(fields=['received_date'], name='received_date_idx'),
            models.Index(fields=['batch_number'], name='batch_number_idx'),
        ]
        verbose_name = "库存批次"

# 物资请求表
class SupplyRequest(BaseModel):
    class RequestStatus(models.TextChoices):
        DRAFT = 'DF', '草稿'
        SUBMITTED = 'SB', '已提交'
        APPROVED = 'AP', '已批准'
        FULFILLED = 'FL', '已完成'
        REJECTED = 'RJ', '已拒绝'
        CANCELLED = 'CN', '已取消'

    request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='requests')
    request_time = models.DateTimeField("申请时间", auto_now_add=True)
    required_by = models.DateTimeField("需求时间")
    status = models.CharField("状态", max_length=2, choices=RequestStatus.choices, default=RequestStatus.DRAFT)
    priority = models.FloatField("优先得分", default=0.5)
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supply_requests')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    approval_time = models.DateTimeField("审批时间", null=True, blank=True)
    comments = models.TextField("备注", blank=True)
    emergency = models.BooleanField("紧急请求", default=False)
    
    def save(self, *args, **kwargs):
        if self.status == self.RequestStatus.APPROVED and not self.approval_time:
            self.approval_time = timezone.now()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-priority', 'required_by']
        verbose_name = "物资请求"

# 物资请求明细表
class RequestItem(BaseModel):
    item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(SupplyRequest, on_delete=models.CASCADE, related_name='items')
    supply = models.ForeignKey(MedicalSupply, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField("需求数量")
    allocated = models.PositiveIntegerField("已分配数量", default=0)
    fulfilled_from_batches = models.ManyToManyField(InventoryBatch, through='ItemFulfillment')
    notes = models.CharField("备注", max_length=255, blank=True)
    priority = models.FloatField("优先得分", default=0.5) # 新增字段
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(allocated__lte=models.F('quantity')),
                name="allocated_le_required"
            )
        ]
        ordering = ['-priority', 'request__required_by'] # 可以考虑将排序移到这里，或保留在ViewSet中
        verbose_name = "请求明细"

# 请求项目的履行记录
class ItemFulfillment(BaseModel):
    fulfillment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_item = models.ForeignKey(RequestItem, on_delete=models.CASCADE)
    inventory_batch = models.ForeignKey(InventoryBatch, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField("分配数量")
    fulfilled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fulfilled_time = models.DateTimeField("履行时间", auto_now_add=True)
    
    class Meta:
        verbose_name = "物资分配记录"
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name="fulfillment_quantity_positive"
            )
        ]

# 库存预警表
class InventoryAlert(BaseModel):
    class AlertType(models.TextChoices):
        LOW_STOCK = 'LS', '库存不足'
        EXPIRING = 'EX', '即将过期'
        EXPIRED = 'ED', '已过期'
        CAPACITY = 'CP', '仓储容量预警'
    
    alert_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='alerts')
    supply = models.ForeignKey(MedicalSupply, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    batch = models.ForeignKey(InventoryBatch, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    alert_type = models.CharField("预警类型", max_length=2, choices=AlertType.choices)
    message = models.TextField("预警信息")
    is_resolved = models.BooleanField("是否解决", default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    resolved_time = models.DateTimeField("解决时间", null=True, blank=True)
    
    class Meta:
        verbose_name = "库存预警"
        indexes = [
            models.Index(fields=['alert_type'], name='alert_type_idx'),
            models.Index(fields=['is_resolved'], name='alert_resolved_idx'),
        ]
