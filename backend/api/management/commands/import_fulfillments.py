from django.core.management.base import BaseCommand
from api.models import RequestItem, InventoryBatch, ItemFulfillment
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = '导入物资分配记录数据'

    def handle(self, *args, **kwargs):
        # 检查是否已有数据，避免重复导入
        if ItemFulfillment.objects.exists():
            self.stdout.write(self.style.WARNING('数据库中已有物资分配记录数据，跳过导入。如需重新导入，请先清空ItemFulfillment表。'))
            return

        # 获取已经有分配数量(allocated > 0)的请求项
        request_items = RequestItem.objects.filter(allocated__gt=0)
        
        if not request_items.exists():
            self.stdout.write(self.style.ERROR('没有找到已分配的请求项。请先运行python manage.py import_requests导入物资请求数据。'))
            return
        
        # 获取所有用户
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR('没有找到用户数据。'))
            return
        
        # 生成分配记录
        fulfillment_count = 0
        
        for item in request_items:
            # 查找该医院该物资的批次
            hospital = item.request.hospital
            supply = item.supply
            
            batches = InventoryBatch.objects.filter(
                hospital=hospital,
                supply=supply,
                quantity__gt=0
            )
            
            if not batches.exists():
                self.stdout.write(self.style.WARNING(f'医院 {hospital.name} 没有 {supply.name} 的可用库存批次，跳过。'))
                continue
            
            # 将已分配数量分配到不同的批次中
            remaining = item.allocated
            batches_list = list(batches)
            
            while remaining > 0 and batches_list:
                # 随机选择一个批次
                batch = random.choice(batches_list)
                
                # 决定从这个批次中分配多少
                # 分配量不能超过批次库存和剩余未分配量
                max_to_allocate = min(batch.quantity, remaining)
                to_allocate = random.randint(1, max_to_allocate) if max_to_allocate > 1 else 1
                
                # 创建分配记录
                fulfillment = ItemFulfillment(
                    request_item=item,
                    inventory_batch=batch,
                    quantity=to_allocate,
                    fulfilled_by=random.choice(users),
                    # 履行时间设置为请求被批准后的一段时间
                    fulfilled_time=item.request.approval_time + timedelta(hours=random.randint(1, 48)) if item.request.approval_time else datetime.now()
                )
                fulfillment.save()
                
                # 更新批次库存（实际应用中可能会有触发器或信号来处理这个逻辑）
                batch.quantity -= to_allocate
                batch.save()
                
                remaining -= to_allocate
                fulfillment_count += 1
                
                # 如果批次的库存用完了，从列表中移除
                if batch.quantity == 0:
                    batches_list.remove(batch)
        
        self.stdout.write(self.style.SUCCESS(f'成功导入 {fulfillment_count} 条物资分配记录数据'))
