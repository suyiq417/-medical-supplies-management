from django.core.management.base import BaseCommand
from api.models import Supplier
import json

class Command(BaseCommand):
    help = '导入供应商数据'

    def handle(self, *args, **kwargs):
        # 检查是否已有数据，避免重复导入
        if Supplier.objects.exists():
            self.stdout.write(self.style.WARNING('数据库中已有供应商数据，跳过导入。如需重新导入，请先清空Supplier表。'))
            return

        suppliers_data = [
            {
                'name': '武汉华康医疗科技有限公司',
                'contact_person': '张伟',
                'contact_info': {
                    'phone': '027-88123456',
                    'email': 'contact@huakang.com',
                    'address': '湖北省武汉市东湖高新区光谷大道77号'
                },
                'address': '湖北省武汉市东湖高新区光谷大道77号',
                'credit_rating': 5
            },
            {
                'name': '华中医药集团有限公司',
                'contact_person': '李明',
                'contact_info': {
                    'phone': '027-82345678',
                    'email': 'service@hzmedical.com',
                    'address': '湖北省武汉市江汉区解放大道1277号'
                },
                'address': '湖北省武汉市江汉区解放大道1277号',
                'credit_rating': 5
            },
            {
                'name': '武汉天立康医疗器械有限公司',
                'contact_person': '王刚',
                'contact_info': {
                    'phone': '027-83456789',
                    'email': 'info@tlkmedical.com',
                    'address': '湖北省武汉市江岸区后湖大道128号'
                },
                'address': '湖北省武汉市江岸区后湖大道128号',
                'credit_rating': 4
            },
            {
                'name': '武汉安泰医疗设备有限公司',
                'contact_person': '陈涛',
                'contact_info': {
                    'phone': '027-84567890',
                    'email': 'contact@antai.com',
                    'address': '湖北省武汉市武昌区和平大道1178号'
                },
                'address': '湖北省武汉市武昌区和平大道1178号',
                'credit_rating': 4
            },
            {
                'name': '湖北仁和药业有限公司',
                'contact_person': '赵敏',
                'contact_info': {
                    'phone': '027-85678901',
                    'email': 'zhaom@renhe.com',
                    'address': '湖北省武汉市洪山区珞瑜路766号'
                },
                'address': '湖北省武汉市洪山区珞瑜路766号',
                'credit_rating': 5
            },
            {
                'name': '武汉博康医疗器械有限公司',
                'contact_person': '孙磊',
                'contact_info': {
                    'phone': '027-86789012',
                    'email': 'sunlei@bokang.com',
                    'address': '湖北省武汉市汉阳区龙阳大道18号'
                },
                'address': '湖北省武汉市汉阳区龙阳大道18号',
                'credit_rating': 3
            },
            {
                'name': '武汉维达医疗用品有限公司',
                'contact_person': '林丽',
                'contact_info': {
                    'phone': '027-87890123',
                    'email': 'linli@vinda.com',
                    'address': '湖北省武汉市黄陂区前川街道107号'
                },
                'address': '湖北省武汉市黄陂区前川街道107号',
                'credit_rating': 4
            },
            {
                'name': '华润武汉医药有限公司',
                'contact_person': '周强',
                'contact_info': {
                    'phone': '027-88901234',
                    'email': 'zhouq@crpharma.com',
                    'address': '湖北省武汉市江汉区新华路219号'
                },
                'address': '湖北省武汉市江汉区新华路219号',
                'credit_rating': 5
            },
            {
                'name': '武汉安健医疗设备有限公司',
                'contact_person': '徐海',
                'contact_info': {
                    'phone': '027-89012345',
                    'email': 'xuh@anjian.com',
                    'address': '湖北省武汉市东西湖区东西湖大道156号'
                },
                'address': '湖北省武汉市东西湖区东西湖大道156号',
                'credit_rating': 3
            },
            {
                'name': '武汉中联医药集团有限公司',
                'contact_person': '郭明',
                'contact_info': {
                    'phone': '027-90123456',
                    'email': 'guom@zlyy.com',
                    'address': '湖北省武汉市青山区建设二路25号'
                },
                'address': '湖北省武汉市青山区建设二路25号',
                'credit_rating': 4
            }
        ]

        # 创建供应商记录
        count = 0
        for data in suppliers_data:
            # 将联系信息转换为JSON
            data['contact_info'] = json.dumps(data['contact_info'])
            
            # 创建供应商记录
            supplier = Supplier(**data)
            supplier.save()
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'成功导入 {count} 家供应商数据'))
