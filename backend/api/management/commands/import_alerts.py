from django.core.management.base import BaseCommand
from api.models import Hospital, MedicalSupply, InventoryBatch, InventoryAlert
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = '导入库存预警数据'

    def handle(self, *args, **kwargs):
        # 检查是否已有数据，避免重复导入
        if InventoryAlert.objects.exists():
            self.stdout.write(self.style.WARNING('数据库中已有库存预警数据，跳过导入。如需重新导入，请先清空InventoryAlert表。'))
            return

        # 获取医院、物资和批次数据
        hospitals = list(Hospital.objects.all())
        supplies = list(MedicalSupply.objects.all())
        batches = list(InventoryBatch.objects.all())
        
        if not hospitals or not supplies or not batches:
            self.stdout.write(self.style.ERROR('缺少必要的数据。请确保已导入医院、物资和库存批次数据。'))
            return
        
        # 获取用户数据用于设置解决人
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.WARNING('没有找到用户数据，预警解决人将设为空。'))
        
        # 当前日期和30天后的日期
        now = datetime.now().date()
        thirty_days_later = now + timedelta(days=30)
        
        # 创建不同类型的预警
        alerts_data = []
        
        # 1. 库存不足预警
        for hospital in hospitals:
            # 随机选择2-5种物资作为库存不足
            low_stock_supplies = random.sample(supplies, random.randint(2, min(5, len(supplies))))
            
            for supply in low_stock_supplies:
                alert_data = {
                    'hospital': hospital,
                    'supply': supply,
                    'batch': None,  # 库存不足预警不关联具体批次
                    'alert_type': 'LS',  # 库存不足
                    'message': f"{hospital.name}的{supply.name}库存低于最低库存水平{supply.min_stock_level}，请及时补充。",
                    'is_resolved': random.choice([True, False]),
                }
                
                # 如果已解决，设置解决人和时间
                if alert_data['is_resolved'] and users:
                    alert_data['resolved_by'] = random.choice(users)
                    alert_data['resolved_time'] = now - timedelta(days=random.randint(1, 10))
                
                alerts_data.append(alert_data)
        
        # 2. 即将过期预警
        # 找出30天内即将过期的批次
        expiring_batches = [b for b in batches if b.expiration_date <= thirty_days_later and b.expiration_date >= now]
        
        # 随机选择其中的一部分作为预警
        expiring_sample = random.sample(expiring_batches, min(len(expiring_batches), 20))
        
        for batch in expiring_sample:
            days_until_expiry = (batch.expiration_date - now).days
            
            alert_data = {
                'hospital': batch.hospital,
                'supply': batch.supply,
                'batch': batch,
                'alert_type': 'EX',  # 即将过期
                'message': f"批次{batch.batch_number}的{batch.supply.name}将在{days_until_expiry}天后过期，请注意使用。",
                'is_resolved': random.choice([True, False]),
            }
            
            # 如果已解决，设置解决人和时间
            if alert_data['is_resolved'] and users:
                alert_data['resolved_by'] = random.choice(users)
                alert_data['resolved_time'] = now - timedelta(days=random.randint(1, 5))
            
            alerts_data.append(alert_data)
        
        # 3. 已过期预警
        # 找出已经过期的批次
        expired_batches = [b for b in batches if b.expiration_date < now]
        
        # 随机选择其中的一部分作为预警
        expired_sample = random.sample(expired_batches, min(len(expired_batches), 10))
        
        for batch in expired_sample:
            days_expired = (now - batch.expiration_date).days
            
            alert_data = {
                'hospital': batch.hospital,
                'supply': batch.supply,
                'batch': batch,
                'alert_type': 'ED',  # 已过期
                'message': f"批次{batch.batch_number}的{batch.supply.name}已过期{days_expired}天，请立即处理。",
                'is_resolved': random.choice([True, False]),
            }
            
            # 如果已解决，设置解决人和时间
            if alert_data['is_resolved'] and users:
                alert_data['resolved_by'] = random.choice(users)
                alert_data['resolved_time'] = now - timedelta(days=random.randint(1, 3))
            
            alerts_data.append(alert_data)
        
        # 4. 仓储容量预警
        # 为接近存储容量上限的医院创建预警
        for hospital in hospitals:
            # 计算使用率
            usage_rate = (hospital.current_capacity / hospital.storage_volume) * 100
            
            # 如果使用率超过80%，创建容量预警
            if usage_rate > 80:
                alert_data = {
                    'hospital': hospital,
                    'supply': None,  # 容量预警不关联具体物资
                    'batch': None,
                    'alert_type': 'CP',  # 仓储容量预警
                    'message': f"{hospital.name}的仓储使用率已达{usage_rate:.1f}%，接近容量上限，请及时调整。",
                    'is_resolved': random.choice([True, False]),
                }
                
                # 如果已解决，设置解决人和时间
                if alert_data['is_resolved'] and users:
                    alert_data['resolved_by'] = random.choice(users)
                    alert_data['resolved_time'] = now - timedelta(days=random.randint(1, 7))
                
                alerts_data.append(alert_data)
        
        # 创建预警记录
        count = 0
        for alert_data in alerts_data:
            alert = InventoryAlert(**alert_data)
            alert.save()
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f'成功导入 {count} 条库存预警数据'))
