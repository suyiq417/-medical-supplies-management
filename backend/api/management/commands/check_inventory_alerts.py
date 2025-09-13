from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from datetime import timedelta
from api.models import Hospital, InventoryBatch, InventoryAlert, MedicalSupply

class Command(BaseCommand):
    help = '检查库存情况并创建预警'

    def handle(self, *args, **kwargs):
        self.check_low_stock()
        self.check_expiring_items()
        self.check_capacity_warning()
        
        self.stdout.write(self.style.SUCCESS('库存预警检查完成'))
    
    def check_low_stock(self):
        """检查库存不足的物资"""
        for supply in MedicalSupply.objects.all():
            total_stock = InventoryBatch.objects.filter(
                supply=supply, 
                is_deleted=False
            ).exclude(
                expiration_date__lt=timezone.now().date()
            ).values('hospital').annotate(
                total=models.Sum('quantity')
            )
            
            for stock in total_stock:
                if stock['total'] < supply.min_stock_level:
                    hospital = Hospital.objects.get(hospital_id=stock['hospital'])
                    
                    # 创建或更新预警
                    alert, created = InventoryAlert.objects.get_or_create(
                        hospital=hospital,
                        supply=supply,
                        alert_type='LS',
                        is_resolved=False,
                        defaults={
                            'message': f'{supply.name}库存不足，当前数量：{stock["total"]}，最低要求：{supply.min_stock_level}'
                        }
                    )
                    
                    if created:
                        self.stdout.write(f'创建库存不足预警: {hospital.name} - {supply.name}')
    
    def check_expiring_items(self):
        """检查即将过期的物资"""
        # 30天内过期的物资
        expiring_date = timezone.now().date() + timedelta(days=30)
        expiring_batches = InventoryBatch.objects.filter(
            expiration_date__lte=expiring_date,
            expiration_date__gt=timezone.now().date(),
            is_deleted=False
        )
        
        for batch in expiring_batches:
            days_left = (batch.expiration_date - timezone.now().date()).days
            
            # 创建或更新预警
            alert, created = InventoryAlert.objects.get_or_create(
                hospital=batch.hospital,
                batch=batch,
                supply=batch.supply,
                alert_type='EX',
                is_resolved=False,
                defaults={
                    'message': f'{batch.supply.name}（批次：{batch.batch_number}）将在{days_left}天后过期'
                }
            )
            
            if created:
                self.stdout.write(f'创建即将过期预警: {batch.hospital.name} - {batch.supply.name}')
    
    def check_capacity_warning(self):
        """检查仓储容量预警"""
        for hospital in Hospital.objects.filter(is_active=True):
            capacity_percentage = (hospital.current_capacity / hospital.storage_volume) * 100
            
            if capacity_percentage >= (100 - hospital.warning_threshold):
                # 创建或更新预警
                alert, created = InventoryAlert.objects.get_or_create(
                    hospital=hospital,
                    alert_type='CP',
                    is_resolved=False,
                    defaults={
                        'message': f'{hospital.name}仓储容量接近上限，当前使用率: {capacity_percentage:.2f}%'
                    }
                )
                
                if created:
                    self.stdout.write(f'创建仓储容量预警: {hospital.name}')
