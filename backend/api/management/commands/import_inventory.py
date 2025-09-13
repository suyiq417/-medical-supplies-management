from django.core.management.base import BaseCommand
from api.models import Hospital, MedicalSupply, Supplier, InventoryBatch
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import random
import string
import json

class Command(BaseCommand):
    help = '导入库存批次数据'

    def handle(self, *args, **kwargs):
        # 检查是否已有数据，避免重复导入
        if InventoryBatch.objects.exists():
            self.stdout.write(self.style.WARNING('数据库中已有库存批次数据，跳过导入。如需重新导入，请先清空InventoryBatch表。'))
            return

        # 检查是否有医院、医疗物资和供应商数据
        hospitals = list(Hospital.objects.all())
        supplies = list(MedicalSupply.objects.all())
        suppliers = list(Supplier.objects.all())
        
        if not hospitals:
            self.stdout.write(self.style.ERROR('没有找到医院数据。请先运行python manage.py import_hospitals导入医院数据。'))
            return
        
        if not supplies:
            self.stdout.write(self.style.ERROR('没有找到医疗物资数据。请先运行python manage.py import_supplies导入医疗物资数据。'))
            return
        
        if not suppliers:
            self.stdout.write(self.style.ERROR('没有找到供应商数据。请先运行python manage.py import_suppliers导入供应商数据。'))
            return
        
        # 获取或创建用户
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('创建了管理员用户: admin'))

        # 创建几个普通用户用于数据关联
        users = [admin_user]
        for i, name in enumerate(['zhang', 'wang', 'li', 'zhao']):
            try:
                user = User.objects.get(username=name)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=name,
                    email=f'{name}@example.com',
                    password=f'{name}123',
                    first_name=name.capitalize(),
                    last_name=['医生', '护士', '库管', '药师'][i % 4]
                )
                self.stdout.write(self.style.SUCCESS(f'创建了普通用户: {name}'))
            users.append(user)

        # 生成批次号的函数
        def generate_batch_number():
            prefix = ''.join(random.choices(string.ascii_uppercase, k=2))
            numbers = ''.join(random.choices(string.digits, k=8))
            return f"{prefix}{numbers}"
        
        # 获取当前日期和过去日期的函数
        now = datetime.now().date()
        
        # 生成库存批次数据
        batches_data = []
        
        # 为每家医院的每种物资创建1-3个批次
        for hospital in hospitals:
            # 为每家医院随机选择15-30种物资
            selected_supplies = random.sample(supplies, random.randint(15, min(30, len(supplies))))
            
            for supply in selected_supplies:
                # 为每种物资创建1-3个批次
                batch_count = random.randint(1, 3)
                
                for _ in range(batch_count):
                    # 生成批次数据
                    production_date = now - timedelta(days=random.randint(30, 365))
                    shelf_life_months = supply.shelf_life
                    expiration_date = production_date + timedelta(days=30 * shelf_life_months)
                    received_date = production_date + timedelta(days=random.randint(5, 30))
                    
                    # 计算数量和价格
                    if supply.category in ['DV']:  # 医疗设备
                        quantity = random.randint(1, 5)
                        unit_price = float(supply.avg_price) * random.uniform(0.9, 1.1)
                    elif supply.category in ['PP', 'RT']:  # 防护装备和检测试剂
                        quantity = random.randint(50, 500)
                        unit_price = float(supply.avg_price) * random.uniform(0.9, 1.1)
                    elif supply.category in ['CS']:  # 一次性耗材
                        quantity = random.randint(500, 5000)
                        unit_price = float(supply.avg_price) * random.uniform(0.9, 1.1)
                    else:  # 药品和其他
                        quantity = random.randint(100, 1000)
                        unit_price = float(supply.avg_price) * random.uniform(0.9, 1.1)
                    
                    # 创建存储条件
                    storage_condition = {
                        'temperature': supply.storage_temp,
                        'humidity': '适宜湿度',
                        'light': '避光' if '避光' in supply.storage_temp else '普通光照',
                        'special_requirements': '无'
                    }
                    
                    batch_data = {
                        'batch_number': generate_batch_number(),
                        'hospital': hospital,
                        'supply': supply,
                        'quantity': quantity,
                        'production_date': production_date,
                        'expiration_date': expiration_date,
                        'storage_condition': json.dumps(storage_condition),
                        'received_date': received_date,
                        'received_by': random.choice(users),
                        'unit_price': unit_price,
                        'supplier': supply.supplier or random.choice(suppliers),
                        'quality_check_passed': True,
                        'notes': f"{supply.name}的库存批次"
                    }
                    
                    batches_data.append(batch_data)
        
        # 创建库存批次记录
        count = 0
        for data in batches_data:
            batch = InventoryBatch(**data)
            batch.save()
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'成功导入 {count} 条库存批次数据'))
