from django.core.management.base import BaseCommand
from api.models import Hospital, MedicalSupply, SupplyRequest, RequestItem
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = '导入物资请求数据'

    def handle(self, *args, **kwargs):
        # 检查是否已有数据，避免重复导入
        if SupplyRequest.objects.exists():
            self.stdout.write(self.style.WARNING('数据库中已有物资请求数据，跳过导入。如需重新导入，请先清空SupplyRequest表。'))
            return

        # 检查是否有医院、医疗物资数据
        hospitals = list(Hospital.objects.all())
        supplies = list(MedicalSupply.objects.all())

        if not hospitals:
            self.stdout.write(self.style.ERROR('没有找到医院数据。请先运行python manage.py import_hospitals导入医院数据。'))
            return

        if not supplies:
            self.stdout.write(self.style.ERROR('没有找到医疗物资数据。请先运行python manage.py import_supplies导入医疗物资数据。'))
            return

        # 获取用户数据
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR('没有找到用户数据。请先运行python manage.py import_inventory导入库存批次数据以创建用户。'))
            return

        # 配置请求数据
        now = datetime.now()
        statuses = ['DF', 'SB', 'AP', 'FL', 'RJ', 'CN']  # 所有可能的状态

        # 创建不同状态的请求
        requests_to_create = []

        # 为每家医院创建5-10个请求
        for hospital in hospitals:
            num_requests = random.randint(5, 10)

            for _ in range(num_requests):
                # 随机选择状态
                status = random.choice(statuses)

                # 设置请求时间，范围为过去3个月内
                request_time = now - timedelta(days=random.randint(0, 90))

                # 设置需求时间，为请求时间后的1-30天
                required_by = request_time + timedelta(days=random.randint(1, 30))

                # 随机生成优先级分数 (0.0 到 1.0 之间)
                priority = round(random.uniform(0.1, 1.0), 5) # 生成0.1到1.0之间的随机浮点数，保留两位小数
                is_emergency = priority >= 0.8  # 优先级分数大于等于0.8的视为紧急请求

                # 随机选择请求者和审批者
                requester = random.choice(users)
                approver = None
                approval_time = None

                # 如果状态为已批准或已完成，设置审批者和审批时间
                if status in ['AP', 'FL']:
                    approver = random.choice([u for u in users if u != requester])
                    # 确保审批时间在请求时间之后，需求时间之前（如果可能）
                    max_approval_delay = (required_by - request_time).days -1
                    if max_approval_delay < 1:
                        max_approval_delay = 1
                    approval_delay = random.randint(1, max_approval_delay)
                    approval_time = request_time + timedelta(days=approval_delay)


                request_data = {
                    'hospital': hospital,
                    'request_time': request_time,
                    'required_by': required_by,
                    'status': status,
                    'priority': priority, # 使用新的浮点数优先级
                    'requester': requester,
                    'approver': approver,
                    'approval_time': approval_time,
                    'comments': f"{hospital.name}的物资请求",
                    'emergency': is_emergency # 根据新的优先级规则判断是否紧急
                }

                requests_to_create.append(request_data)

        # 创建请求记录
        request_count = 0
        item_count = 0

        for request_data in requests_to_create:
            # 创建请求
            request = SupplyRequest(**request_data)
            request.save()
            request_count += 1

            # 为每个请求添加3-8个请求项
            num_items = random.randint(3, 8)
            # 确保请求的物资数量不超过总物资数量
            if num_items > len(supplies):
                num_items = len(supplies)
            selected_supplies = random.sample(supplies, num_items)

            for supply in selected_supplies:
                # 设置请求数量
                if supply.category in ['DV']:  # 医疗设备
                    quantity = random.randint(1, 3)
                elif supply.category in ['PP', 'RT']:  # 防护装备和检测试剂
                    quantity = random.randint(20, 200)
                elif supply.category in ['CS']:  # 一次性耗材
                    quantity = random.randint(100, 1000)
                else:  # 药品和其他
                    quantity = random.randint(50, 500)

                # 如果请求已完成，则将已分配数量设为请求数量
                # 如果请求已批准但未完成，则将已分配数量设为请求数量的一部分
                # 其他状态的请求，已分配数量为0
                allocated = 0
                if request.status == 'FL':
                    allocated = quantity
                elif request.status == 'AP':
                    # 分配数量在0到请求数量之间随机
                    allocated = random.randint(0, quantity)

                # 为 RequestItem 设置随机初始优先级
                item_priority = round(random.uniform(0.1, 1.0), 5) 

                item_data = {
                    'request': request,
                    'supply': supply,
                    'quantity': quantity,
                    'allocated': allocated,
                    'notes': f"请求{supply.name}",
                    'priority': item_priority # 添加这一行
                }

                # 创建请求项
                item = RequestItem(**item_data)
                item.save()
                item_count += 1

        self.stdout.write(self.style.SUCCESS(f'成功导入 {request_count} 条物资请求数据，共 {item_count} 个请求项目'))
