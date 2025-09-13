import json
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from api.models import Hospital

class Command(BaseCommand):
    help = '导入武汉市医院数据'

    def handle(self, *args, **kwargs):
        # 检查是否已有数据，避免重复导入
        if Hospital.objects.exists():
            self.stdout.write(self.style.WARNING('数据库中已有医院数据，跳过导入。如需重新导入，请先清空Hospital表。'))
            return

        hospitals_data = [
            {
                'org_code': 'WH001',
                'name': '华中科技大学同济医学院附属同济医院',
                'level': 9,  # 三甲医院
                'address': '湖北省武汉市硚口区解放大道1095号',
                'geo_location': [114.269, 30.578],  # 经度, 纬度
                'contact_info': {
                    'phone': '027-83662688',
                    'email': 'contact@tjh.com.cn',
                    'website': 'www.tjh.com.cn'
                },
                'storage_volume': 10000.00,
                'current_capacity': 7500.00,
                'region': '硚口区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH002',
                'name': '华中科技大学同济医学院附属协和医院',
                'level': 9,  # 三甲医院
                'address': '湖北省武汉市江汉区解放大道1277号',
                'geo_location': [114.282, 30.590],
                'contact_info': {
                    'phone': '027-85726114',
                    'email': 'contact@hust-xh.com',
                    'website': 'www.hust-xh.com'
                },
                'storage_volume': 9500.00,
                'current_capacity': 7000.00,
                'region': '江汉区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH003',
                'name': '武汉大学人民医院',
                'level': 9,  # 三甲医院
                'address': '湖北省武汉市武昌区解放路238号',
                'geo_location': [114.324, 30.542],
                'contact_info': {
                    'phone': '027-88041911',
                    'email': 'contact@rmhospital.com',
                    'website': 'www.rmhospital.com'
                },
                'storage_volume': 8000.00,
                'current_capacity': 5500.00,
                'region': '武昌区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH004',
                'name': '武汉大学中南医院',
                'level': 9,  # 三甲医院
                'address': '湖北省武汉市武昌区东湖路169号',
                'geo_location': [114.340, 30.536],
                'contact_info': {
                    'phone': '027-67813000',
                    'email': 'contact@znhospital.com',
                    'website': 'www.znhospital.com'
                },
                'storage_volume': 7500.00,
                'current_capacity': 5000.00,
                'region': '武昌区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH005',
                'name': '湖北省人民医院',
                'level': 9,  # 三甲医院
                'address': '湖北省武汉市江岸区武汉解放大道750号',
                'geo_location': [114.303, 30.580],
                'contact_info': {
                    'phone': '027-68758312',
                    'email': 'contact@hbsrmyy.com',
                    'website': 'www.hbsrmyy.com'
                },
                'storage_volume': 7000.00,
                'current_capacity': 4500.00,
                'region': '江岸区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH006',
                'name': '武汉市第一医院',
                'level': 9,  # 三甲医院
                'address': '湖北省武汉市硚口区中山大道215号',
                'geo_location': [114.264, 30.582],
                'contact_info': {
                    'phone': '027-85832018',
                    'email': 'contact@whsyy.com',
                    'website': 'www.whsyy.com'
                },
                'storage_volume': 6500.00,
                'current_capacity': 4000.00,
                'region': '硚口区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH007',
                'name': '武汉市中心医院',
                'level': 9,  # 三甲医院
                'address': '湖北省武汉市江岸区胜利街26号',
                'geo_location': [114.298, 30.593],
                'contact_info': {
                    'phone': '027-82211246',
                    'email': 'contact@whzxyy.com',
                    'website': 'www.whzxyy.com'
                },
                'storage_volume': 6000.00,
                'current_capacity': 3800.00,
                'region': '江岸区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH008',
                'name': '武汉市第三医院',
                'level': 9,  # 三甲医院
                'address': '湖北省武汉市武昌区彭刘杨路241号',
                'geo_location': [114.314, 30.561],
                'contact_info': {
                    'phone': '027-68894466',
                    'email': 'contact@whsdsyy.com',
                    'website': 'www.whsdsyy.com'
                },
                'storage_volume': 5500.00,
                'current_capacity': 3600.00,
                'region': '武昌区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH009',
                'name': '武汉市第四医院',
                'level': 8,  # 三乙医院
                'address': '湖北省武汉市硚口区汉正街473号',
                'geo_location': [114.272, 30.585],
                'contact_info': {
                    'phone': '027-83782519',
                    'email': 'contact@wh4h.com',
                    'website': 'www.wh4h.com'
                },
                'storage_volume': 4500.00,
                'current_capacity': 2800.00,
                'region': '硚口区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH010',
                'name': '武汉市第五医院',
                'level': 7,  # 二甲医院
                'address': '湖北省武汉市汉阳区显正街122号',
                'geo_location': [114.265, 30.553],
                'contact_info': {
                    'phone': '027-84812018',
                    'email': 'contact@wh5hospital.com',
                    'website': 'www.wh5hospital.com'
                },
                'storage_volume': 4000.00,
                'current_capacity': 2500.00,
                'region': '汉阳区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH011',
                'name': '武汉市第六医院',
                'level': 7,  # 二甲医院
                'address': '湖北省武汉市江汉区香港路168号',
                'geo_location': [114.281, 30.585],
                'contact_info': {
                    'phone': '027-82789509',
                    'email': 'contact@wh6h.com',
                    'website': 'www.wh6h.com'
                },
                'storage_volume': 3500.00,
                'current_capacity': 2300.00,
                'region': '江汉区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH012',
                'name': '武汉市第七医院',
                'level': 7,  # 二甲医院
                'address': '湖北省武汉市武昌区小洪山路176号',
                'geo_location': [114.357, 30.545],
                'contact_info': {
                    'phone': '027-87875107',
                    'email': 'contact@wh7yy.com',
                    'website': 'www.wh7yy.com'
                },
                'storage_volume': 3200.00,
                'current_capacity': 2100.00,
                'region': '武昌区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH013',
                'name': '武汉市第八医院',
                'level': 7,  # 二甲医院
                'address': '湖北省武汉市汉口区汉江路68号',
                'geo_location': [114.283, 30.622],
                'contact_info': {
                    'phone': '027-83522888',
                    'email': 'contact@wh8h.com',
                    'website': 'www.wh8h.com'
                },
                'storage_volume': 3000.00,
                'current_capacity': 1900.00,
                'region': '江岸区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH014',
                'name': '华中科技大学同济医学院附属梨园医院',
                'level': 7,  # 二甲医院
                'address': '湖北省武汉市武昌区东湖路312号',
                'geo_location': [114.342, 30.549],
                'contact_info': {
                    'phone': '027-86793220',
                    'email': 'contact@liyuanyy.com',
                    'website': 'www.liyuanyy.com'
                },
                'storage_volume': 2800.00,
                'current_capacity': 1800.00,
                'region': '武昌区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH015',
                'name': '武汉亚洲心脏病医院',
                'level': 7,  # 二甲医院
                'address': '湖北省武汉市江汉区京汉大道753号',
                'geo_location': [114.289, 30.588],
                'contact_info': {
                    'phone': '027-85743333',
                    'email': 'contact@yzxzbyy.com',
                    'website': 'www.yzxzbyy.com'
                },
                'storage_volume': 2500.00,
                'current_capacity': 1600.00,
                'region': '江汉区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH016',
                'name': '武汉大学口腔医院',
                'level': 9,  # 三甲医院
                'address': '湖北省武汉市洪山区珞喻路237号',
                'geo_location': [114.354, 30.522],
                'contact_info': {
                    'phone': '027-87686000',
                    'email': 'contact@whdxkqyy.com',
                    'website': 'www.whdxkqyy.com'
                },
                'storage_volume': 2300.00,
                'current_capacity': 1500.00,
                'region': '洪山区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH017',
                'name': '武汉市中医医院',
                'level': 9,  # 三甲医院
                'address': '湖北省武汉市江岸区黎黄陂路49号',
                'geo_location': [114.308, 30.599],
                'contact_info': {
                    'phone': '027-82857342',
                    'email': 'contact@whszyyy.com',
                    'website': 'www.whszyyy.com'
                },
                'storage_volume': 4000.00,
                'current_capacity': 2800.00,
                'region': '江岸区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH018',
                'name': '武汉儿童医院',
                'level': 9,  # 三甲医院
                'address': '湖北省武汉市江岸区香港路100号',
                'geo_location': [114.298, 30.587],
                'contact_info': {
                    'phone': '027-82433350',
                    'email': 'contact@whetyyy.com',
                    'website': 'www.whetyyy.com'
                },
                'storage_volume': 3800.00,
                'current_capacity': 2700.00,
                'region': '江岸区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH019',
                'name': '武汉市妇幼保健院',
                'level': 9,  # 三甲医院
                'address': '湖北省武汉市江岸区香港路506号',
                'geo_location': [114.297, 30.598],
                'contact_info': {
                    'phone': '027-85269595',
                    'email': 'contact@whfybj.com',
                    'website': 'www.whfybj.com'
                },
                'storage_volume': 3500.00,
                'current_capacity': 2400.00,
                'region': '江岸区',
                'is_active': True,
                'warning_threshold': 15.00
            },
            {
                'org_code': 'WH020',
                'name': '武汉科技大学附属天佑医院',
                'level': 9,  # 三甲医院
                'address': '湖北省武汉市武昌区丁字桥路9号',
                'geo_location': [114.318, 30.568],
                'contact_info': {
                    'phone': '027-51228666',
                    'email': 'contact@whtyh.com',
                    'website': 'www.whtyh.com'
                },
                'storage_volume': 3200.00,
                'current_capacity': 2200.00,
                'region': '武昌区',
                'is_active': True,
                'warning_threshold': 15.00
            }
        ]

        # 创建医院记录
        count = 0
        for data in hospitals_data:
            # 创建地理位置Point对象
            point = Point(data['geo_location'][0], data['geo_location'][1])
            
            # 将联系信息转换为JSON字符串，如果它是一个字典的话
            if isinstance(data['contact_info'], dict):
                 data['contact_info'] = json.dumps(data['contact_info'], ensure_ascii=False) # 添加 ensure_ascii=False 以支持中文

            # 准备用于创建Hospital实例的数据
            hospital_data = {
                'org_code': data['org_code'],
                'name': data['name'],
                'level': data['level'],
                'address': data['address'],
                'geo_location': point, # 使用创建的Point对象
                'contact_info': data['contact_info'],
                'storage_volume': data['storage_volume'],
                'current_capacity': data['current_capacity'],
                'region': data['region'],
                'is_active': data['is_active'],
                'warning_threshold': data['warning_threshold']
            }

            # 创建医院记录
            hospital = Hospital(**hospital_data)
            hospital.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'成功导入 {count} 家武汉市医院数据'))
