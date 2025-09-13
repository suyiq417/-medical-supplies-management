# filepath: api/management/commands/recalculate_priorities.py
from django.core.management.base import BaseCommand
from django.db.models import Q, F, Value, ExpressionWrapper, fields
from django.db.models.functions import Coalesce
from api.models import MedicalSupply, SupplyRequest, RequestItem
from api.views import calculate_and_update_priorities # 导入计算函数
import time

class Command(BaseCommand):
    help = '重新计算所有相关物资请求的优先级得分'

    def handle(self, *args, **kwargs):
        self.stdout.write("开始重新计算物资请求优先级...")

        # 查找所有需要重新计算优先级的物资 UNSPSC 代码
        # 条件：请求状态为 '已提交' 或 '已批准'，且请求数量 > 已分配数量
        relevant_supply_codes = RequestItem.objects.filter(
            Q(request__status=SupplyRequest.RequestStatus.SUBMITTED) |
            Q(request__status=SupplyRequest.RequestStatus.APPROVED),
            is_deleted=False,
            quantity__gt=Coalesce(F('allocated'), Value(0)) # 确保请求量大于已分配量
        ).values_list('supply__unspsc_code', flat=True).distinct()

        supply_codes_list = list(relevant_supply_codes)
        total_supplies = len(supply_codes_list)

        if not total_supplies:
            self.stdout.write(self.style.WARNING("没有找到需要重新计算优先级的物资请求。"))
            return

        self.stdout.write(f"找到 {total_supplies} 种物资需要重新计算优先级。")

        processed_count = 0
        start_time = time.time()

        for supply_code in supply_codes_list:
            if not supply_code:
                continue # 跳过空的 supply_code

            processed_count += 1
            self.stdout.write(f"({processed_count}/{total_supplies}) 正在处理物资代码: {supply_code}")
            try:
                # 调用视图中的函数来计算和更新优先级
                calculate_and_update_priorities(supply_code)
                self.stdout.write(self.style.SUCCESS(f"  - 物资 {supply_code} 的优先级已更新。"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  - 处理物资 {supply_code} 时出错: {e}"))
                import traceback
                traceback.print_exc() # 打印详细错误信息

        end_time = time.time()
        duration = end_time - start_time
        self.stdout.write(self.style.SUCCESS(f"所有相关物资的优先级重新计算完成。耗时: {duration:.2f} 秒。"))
