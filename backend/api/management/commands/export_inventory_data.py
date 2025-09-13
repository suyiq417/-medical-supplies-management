import csv
from django.core.management.base import BaseCommand
from django.utils import timezone
from collections import defaultdict
from datetime import date
from django.db.models import Sum, F, ExpressionWrapper, fields

# 导入正确的模型
try:
    # 确保导入的模型名称与你的 models.py 文件一致
    from api.models import Hospital, InventoryBatch, MedicalSupply, SupplyRequest, RequestItem
except ImportError:
    raise ImportError("无法从 api.models 导入 Hospital, InventoryBatch, MedicalSupply, SupplyRequest 或 RequestItem。请检查模型位置和名称。")

class Command(BaseCommand):
    help = '导出医院库存数据及待处理物资请求到 CSV 文件。'

    def handle(self, *args, **options):
        self.stdout.write("正在导出医院等级...")
        self._export_hospital_levels()

        self.stdout.write("正在导出库存总量...")
        self._export_inventory_details()

        self.stdout.write("正在导出平均过期时间（剩余天数）...")
        self._export_average_expiration()

        self.stdout.write("正在导出待处理的物资请求...")
        self._export_pending_supply_requests()

        self.stdout.write(self.style.SUCCESS('数据已成功导出。'))

    def _export_hospital_levels(self):
        """导出医院名称和等级"""
        try:
            hospitals = Hospital.objects.values('name', 'level').order_by('name')
            filepath = 'hospital_levels.csv'
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['hospital_name', 'level']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for hospital in hospitals:
                    level_display = Hospital.HospitalLevel(hospital['level']).label
                    writer.writerow({'hospital_name': hospital['name'], 'level': level_display})
            self.stdout.write(self.style.SUCCESS(f' -> {filepath}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"导出医院等级时出错: {e}"))


    def _export_inventory_details(self):
        """导出各医院各物资的总库存量、医院容量预警阈值及物资全局最低库存"""
        try:
            # 查询时包含医院阈值和物资最低库存
            inventory_summary = InventoryBatch.objects.values(
                'hospital__name',
                'supply__name',
                'supply__min_stock_level'      # <--- 物资全局最低库存 (单位)
            ).annotate(
                total_quantity=Sum('quantity')
            ).order_by('hospital__name', 'supply__name')

            filepath = 'inventory_summary.csv'
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                # 添加两个阈值字段名
                fieldnames = [
                    'hospital_name',
                    'supply_name',
                    'total_quantity',
                    'supply_global_min_stock_level'              # <--- 物资阈值列名
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for item in inventory_summary:
                     writer.writerow({
                        'hospital_name': item['hospital__name'],
                        'supply_name': item['supply__name'],
                        'total_quantity': item['total_quantity'],
                        'supply_global_min_stock_level': item['supply__min_stock_level']                   # <--- 物资阈值数据
                    })
            self.stdout.write(self.style.SUCCESS(f' -> {filepath}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"导出库存总量及阈值时出错: {e}"))


    def _export_average_expiration(self):
        """导出各医院各物资的平均剩余过期天数"""
        try:
            # 使用正确的字段名 'supply' 和 'supply__name'
            inventory_items = InventoryBatch.objects.select_related('hospital', 'supply').filter( # <--- 修改这里
                expiration_date__isnull=False
            ).values(
                'hospital__name',
                'supply__name', # <--- 修改这里
                'expiration_date',
                'quantity'
            ).order_by('hospital__name', 'supply__name') # <--- 修改这里

            grouped_data = defaultdict(lambda: defaultdict(list))
            for item in inventory_items:
                # 使用正确的键 'supply__name'
                grouped_data[item['hospital__name']][item['supply__name']].append( # <--- 修改这里
                    (item['expiration_date'], item['quantity'])
                )

            avg_expiry_data = []
            today = timezone.now().date()

            for hospital_name, supplies in grouped_data.items():
                for supply_name, expiry_batches in supplies.items():
                    if not expiry_batches:
                        continue

                    total_days_remaining = 0
                    valid_batches_count = 0

                    for expiry_date, quantity in expiry_batches:
                        current_date = expiry_date
                        if isinstance(current_date, date):
                            days_remaining = (current_date - today).days
                            total_days_remaining += days_remaining
                            valid_batches_count += 1

                    if valid_batches_count > 0:
                        avg_days_remaining = total_days_remaining / valid_batches_count
                        avg_expiry_data.append({
                            'hospital_name': hospital_name,
                            'supply_name': supply_name, # 保持 supply_name
                            'avg_days_remaining': round(avg_days_remaining, 2)
                        })

            filepath = 'average_expiration.csv'
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['hospital_name', 'supply_name', 'avg_days_remaining']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(avg_expiry_data)
            self.stdout.write(self.style.SUCCESS(f' -> {filepath}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"导出平均过期时间时出错: {e}"))

    def _export_pending_supply_requests(self):
        """导出待处理（已提交、已批准）的物资请求及其明细到 CSV 文件"""
        try:
            # 定义哪些状态是“待处理” - 仅包括已提交和已批准
            pending_statuses = [
                SupplyRequest.RequestStatus.SUBMITTED,
                SupplyRequest.RequestStatus.APPROVED,
            ]

            # 查询所有待处理请求的明细项
            pending_items = RequestItem.objects.filter(
                request__status__in=pending_statuses
            ).select_related(
                'request',          # 获取关联的 SupplyRequest
                'request__hospital',# 通过 SupplyRequest 获取关联的 Hospital
                'supply'            # 获取关联的 MedicalSupply
            ).order_by(
                'request__hospital__name', # 按医院名称排序
                'request__request_time',   # 按请求时间排序
                'supply__name'             # 按物资名称排序
            )

            if not pending_items.exists():
                self.stdout.write(self.style.WARNING('没有找到状态为“已提交”或“已批准”的物资请求。'))
                return

            filepath = 'pending_supply_requests.csv'
            self.stdout.write(f"正在导出状态为“已提交”或“已批准”的物资请求到 {filepath}...")

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                # 定义 CSV 文件头
                fieldnames = [
                    'hospital_name',
                    'request_id',
                    'request_time',
                    'required_by',
                    'status',
                    'priority',
                    'emergency',
                    'supply_name',
                    'requested_quantity',
                    'allocated_quantity', # 也导出已分配数量作为参考
                    'requester_username',
                    'comments'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                # 遍历查询结果并写入 CSV
                for item in pending_items:
                    request = item.request # 获取关联的请求对象
                    writer.writerow({
                        'hospital_name': request.hospital.name,
                        'request_id': str(request.request_id), # UUID 转为字符串
                        'request_time': request.request_time.strftime('%Y-%m-%d %H:%M:%S') if request.request_time else '',
                        'required_by': request.required_by.strftime('%Y-%m-%d %H:%M:%S') if request.required_by else '',
                        'status': request.get_status_display(), # 获取状态的显示名称
                        'priority': request.priority,
                        'emergency': '是' if request.emergency else '否',
                        'supply_name': item.supply.name,
                        'requested_quantity': item.quantity,
                        'allocated_quantity': item.allocated,
                        'requester_username': request.requester.username if request.requester else 'N/A',
                        'comments': request.comments
                    })

            self.stdout.write(self.style.SUCCESS(f'成功导出 {pending_items.count()} 条状态为“已提交”或“已批准”的请求明细到 {filepath}'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"导出待处理请求时出错: {e}"))
