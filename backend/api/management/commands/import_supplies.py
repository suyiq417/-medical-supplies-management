from django.core.management.base import BaseCommand
from api.models import MedicalSupply, Supplier
import random

class Command(BaseCommand):
    help = '导入医疗物资数据'

    def handle(self, *args, **kwargs):
        # 检查是否已有数据，避免重复导入
        if MedicalSupply.objects.exists():
            self.stdout.write(self.style.WARNING('数据库中已有医疗物资数据，跳过导入。如需重新导入，请先清空MedicalSupply表。'))
            return

        # 检查是否有供应商数据
        suppliers = list(Supplier.objects.all())
        if not suppliers:
            self.stdout.write(self.style.ERROR('没有找到供应商数据。请先运行python manage.py import_suppliers导入供应商数据。'))
            return

        supplies_data = [
            # 药品类
            {
                'unspsc_code': 'DG51091101',
                'name': '阿司匹林肠溶片',
                'category': 'DG',
                'unit': '盒',
                'standard': '100mg*30片/盒',
                'shelf_life': 24,
                'storage_temp': '常温',
                'is_controlled': False,
                'description': '用于缓解轻至中度疼痛，如头痛、牙痛、肌肉痛、神经痛、关节痛、痛经等',
                'avg_price': 8.50,
                'min_stock_level': 1000
            },
            {
                'unspsc_code': 'DG51091102',
                'name': '布洛芬缓释胶囊',
                'category': 'DG',
                'unit': '盒',
                'standard': '300mg*10粒/盒',
                'shelf_life': 24,
                'storage_temp': '常温',
                'is_controlled': False,
                'description': '用于缓解轻至中度疼痛如头痛、关节痛、偏头痛、牙痛、肌肉痛等',
                'avg_price': 15.80,
                'min_stock_level': 800
            },
            {
                'unspsc_code': 'DG51091103',
                'name': '对乙酰氨基酚片',
                'category': 'DG',
                'unit': '瓶',
                'standard': '500mg*100片/瓶',
                'shelf_life': 36,
                'storage_temp': '常温',
                'is_controlled': False,
                'description': '适用于感冒或流感引起的发热，也可用于轻至中度疼痛',
                'avg_price': 12.30,
                'min_stock_level': 1200
            },
            {
                'unspsc_code': 'DG51091104',
                'name': '盐酸氨溴索口服溶液',
                'category': 'DG',
                'unit': '瓶',
                'standard': '100ml:0.3g/瓶',
                'shelf_life': 36,
                'storage_temp': '常温避光',
                'is_controlled': False,
                'description': '用于痰液粘稠、咳痰困难等',
                'avg_price': 25.60,
                'min_stock_level': 500
            },
            {
                'unspsc_code': 'DG51091105',
                'name': '注射用青霉素钠',
                'category': 'DG',
                'unit': '支',
                'standard': '80万单位/支',
                'shelf_life': 24,
                'storage_temp': '2-8°C',
                'is_controlled': True,
                'description': '用于敏感菌所致的各种感染',
                'avg_price': 3.80,
                'min_stock_level': 2000
            },
            {
                'unspsc_code': 'DG51091106',
                'name': '头孢克洛胶囊',
                'category': 'DG',
                'unit': '盒',
                'standard': '250mg*6粒/盒',
                'shelf_life': 24,
                'storage_temp': '常温避光',
                'is_controlled': True,
                'description': '用于敏感菌所致的呼吸道感染、泌尿道感染等',
                'avg_price': 28.50,
                'min_stock_level': 600
            },
            {
                'unspsc_code': 'DG51091107',
                'name': '盐酸莫西沙星片',
                'category': 'DG',
                'unit': '盒',
                'standard': '400mg*5片/盒',
                'shelf_life': 36,
                'storage_temp': '常温避光',
                'is_controlled': True,
                'description': '用于成人（≥18岁）敏感菌引起的感染',
                'avg_price': 78.90,
                'min_stock_level': 300
            },
            {
                'unspsc_code': 'DG51091108',
                'name': '盐酸左氧氟沙星注射液',
                'category': 'DG',
                'unit': '支',
                'standard': '200mg:100ml/支',
                'shelf_life': 24,
                'storage_temp': '常温避光',
                'is_controlled': True,
                'description': '用于敏感菌所致的各种感染',
                'avg_price': 35.60,
                'min_stock_level': 500
            },
            {
                'unspsc_code': 'DG51091109',
                'name': '盐酸多巴胺注射液',
                'category': 'DG',
                'unit': '支',
                'standard': '2ml:20mg/支',
                'shelf_life': 24,
                'storage_temp': '2-8°C',
                'is_controlled': True,
                'description': '用于各种原因引起的休克、心肌梗死所致的低血压等',
                'avg_price': 2.40,
                'min_stock_level': 1500
            },
            {
                'unspsc_code': 'DG51091110',
                'name': '琥珀酸美托洛尔缓释片',
                'category': 'DG',
                'unit': '盒',
                'standard': '47.5mg*7片/盒',
                'shelf_life': 36,
                'storage_temp': '常温避光',
                'is_controlled': False,
                'description': '用于高血压、心绞痛等',
                'avg_price': 38.50,
                'min_stock_level': 400
            },
            
            # 医疗设备类
            {
                'unspsc_code': 'DV42201601',
                'name': '心电监护仪',
                'category': 'DV',
                'unit': '台',
                'standard': 'ECG-1210',
                'shelf_life': 120,
                'storage_temp': '常温',
                'is_controlled': False,
                'description': '用于监测患者的心电图、血氧饱和度、无创血压等生命体征',
                'avg_price': 25000.00,
                'min_stock_level': 10
            },
            {
                'unspsc_code': 'DV42201602',
                'name': '呼吸机',
                'category': 'DV',
                'unit': '台',
                'standard': 'VENT-5000',
                'shelf_life': 120,
                'storage_temp': '常温',
                'is_controlled': True,
                'description': '用于呼吸功能不全患者的辅助呼吸',
                'avg_price': 150000.00,
                'min_stock_level': 5
            },
            {
                'unspsc_code': 'DV42201603',
                'name': '输液泵',
                'category': 'DV',
                'unit': '台',
                'standard': 'IP-2000',
                'shelf_life': 120,
                'storage_temp': '常温',
                'is_controlled': False,
                'description': '用于精确控制静脉输液的速度和剂量',
                'avg_price': 8000.00,
                'min_stock_level': 20
            },
            {
                'unspsc_code': 'DV42201604',
                'name': '便携式B超机',
                'category': 'DV',
                'unit': '台',
                'standard': 'USG-3300',
                'shelf_life': 120,
                'storage_temp': '常温',
                'is_controlled': False,
                'description': '用于进行超声诊断检查',
                'avg_price': 80000.00,
                'min_stock_level': 3
            },
            {
                'unspsc_code': 'DV42201605',
                'name': '血液透析机',
                'category': 'DV',
                'unit': '台',
                'standard': 'HDM-4000',
                'shelf_life': 120,
                'storage_temp': '常温',
                'is_controlled': True,
                'description': '用于肾功能衰竭患者的血液透析治疗',
                'avg_price': 120000.00,
                'min_stock_level': 2
            },
            
            # 防护装备类
            {
                'unspsc_code': 'PP46181501',
                'name': 'N95医用防护口罩',
                'category': 'PP',
                'unit': '个',
                'standard': 'KN95',
                'shelf_life': 24,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '用于医护人员防护，阻隔飞沫、粉尘等',
                'avg_price': 8.50,
                'min_stock_level': 5000
            },
            {
                'unspsc_code': 'PP46181502',
                'name': '医用防护服',
                'category': 'PP',
                'unit': '套',
                'standard': 'GB 19082-2009',
                'shelf_life': 36,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '一次性使用，用于医护人员在隔离环境中的个人防护',
                'avg_price': 120.00,
                'min_stock_level': 1000
            },
            {
                'unspsc_code': 'PP46181503',
                'name': '医用防护面罩',
                'category': 'PP',
                'unit': '个',
                'standard': 'YY/T 0981-2013',
                'shelf_life': 36,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '用于保护面部免受液体飞溅',
                'avg_price': 35.00,
                'min_stock_level': 800
            },
            {
                'unspsc_code': 'PP46181504',
                'name': '医用橡胶检查手套',
                'category': 'PP',
                'unit': '双',
                'standard': 'GB 10213-2006',
                'shelf_life': 36,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '一次性使用，用于医疗检查和护理',
                'avg_price': 2.50,
                'min_stock_level': 10000
            },
            {
                'unspsc_code': 'PP46181505',
                'name': '医用防水靴套',
                'category': 'PP',
                'unit': '双',
                'standard': 'YY/T 0981-2013',
                'shelf_life': 36,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '一次性使用，防水防滑',
                'avg_price': 15.00,
                'min_stock_level': 1000
            },
            
            # 检测试剂类
            {
                'unspsc_code': 'RT41115801',
                'name': '新型冠状病毒核酸检测试剂盒',
                'category': 'RT',
                'unit': '盒',
                'standard': '24人份/盒',
                'shelf_life': 12,
                'storage_temp': '-20°C',
                'is_controlled': True,
                'description': '用于体外定性检测人鼻咽拭子、咽拭子样本中的新型冠状病毒RNA',
                'avg_price': 1800.00,
                'min_stock_level': 100
            },
            {
                'unspsc_code': 'RT41115802',
                'name': '甲型流感病毒抗原检测试剂盒',
                'category': 'RT',
                'unit': '盒',
                'standard': '20人份/盒',
                'shelf_life': 12,
                'storage_temp': '2-8°C',
                'is_controlled': False,
                'description': '用于体外定性检测人鼻咽拭子、咽拭子样本中的甲型流感病毒抗原',
                'avg_price': 600.00,
                'min_stock_level': 50
            },
            {
                'unspsc_code': 'RT41115803',
                'name': '血糖测试条',
                'category': 'RT',
                'unit': '盒',
                'standard': '50条/盒',
                'shelf_life': 18,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '用于血糖仪检测血糖值',
                'avg_price': 150.00,
                'min_stock_level': 200
            },
            {
                'unspsc_code': 'RT41115804',
                'name': '肝功能生化检测试剂盒',
                'category': 'RT',
                'unit': '盒',
                'standard': '100测试/盒',
                'shelf_life': 12,
                'storage_temp': '2-8°C',
                'is_controlled': False,
                'description': '用于检测肝功能指标',
                'avg_price': 1200.00,
                'min_stock_level': 30
            },
            {
                'unspsc_code': 'RT41115805',
                'name': '心肌肌钙蛋白I检测试剂盒',
                'category': 'RT',
                'unit': '盒',
                'standard': '25测试/盒',
                'shelf_life': 12,
                'storage_temp': '2-8°C',
                'is_controlled': False,
                'description': '用于心肌梗死的辅助诊断',
                'avg_price': 1800.00,
                'min_stock_level': 20
            },
            
            # 一次性耗材类
            {
                'unspsc_code': 'CS42142501',
                'name': '一次性注射器',
                'category': 'CS',
                'unit': '个',
                'standard': '5ml',
                'shelf_life': 60,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '用于注射药液或抽取血液',
                'avg_price': 0.80,
                'min_stock_level': 20000
            },
            {
                'unspsc_code': 'CS42142502',
                'name': '一次性输液器',
                'category': 'CS',
                'unit': '套',
                'standard': '带针',
                'shelf_life': 60,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '用于静脉输液',
                'avg_price': 3.50,
                'min_stock_level': 10000
            },
            {
                'unspsc_code': 'CS42142503',
                'name': '医用棉签',
                'category': 'CS',
                'unit': '包',
                'standard': '100支/包',
                'shelf_life': 60,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '用于医疗处理和采样',
                'avg_price': 8.00,
                'min_stock_level': 2000
            },
            {
                'unspsc_code': 'CS42142504',
                'name': '医用纱布',
                'category': 'CS',
                'unit': '包',
                'standard': '7.5cm×7.5cm×8层×10片/包',
                'shelf_life': 60,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '用于伤口护理和治疗',
                'avg_price': 12.00,
                'min_stock_level': 3000
            },
            {
                'unspsc_code': 'CS42142505',
                'name': '采血管',
                'category': 'CS',
                'unit': '支',
                'standard': '5ml',
                'shelf_life': 36,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '用于采集血液样本',
                'avg_price': 2.50,
                'min_stock_level': 5000
            },
            
            # 其他类
            {
                'unspsc_code': 'OT51102301',
                'name': '医用冰袋',
                'category': 'OT',
                'unit': '个',
                'standard': '中号',
                'shelf_life': 60,
                'storage_temp': '常温',
                'is_controlled': False,
                'description': '用于物理降温和消肿',
                'avg_price': 25.00,
                'min_stock_level': 500
            },
            {
                'unspsc_code': 'OT51102302',
                'name': '医用胶带',
                'category': 'OT',
                'unit': '卷',
                'standard': '1.25cm×9.1m',
                'shelf_life': 36,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '用于固定敷料和医疗器械',
                'avg_price': 15.00,
                'min_stock_level': 1000
            },
            {
                'unspsc_code': 'OT51102303',
                'name': '医用床单',
                'category': 'OT',
                'unit': '件',
                'standard': '180cm×90cm',
                'shelf_life': 60,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '用于病床保护和患者舒适',
                'avg_price': 45.00,
                'min_stock_level': 300
            },
            {
                'unspsc_code': 'OT51102304',
                'name': '病历夹',
                'category': 'OT',
                'unit': '个',
                'standard': 'A4',
                'shelf_life': 120,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '用于管理患者病历和医疗记录',
                'avg_price': 18.00,
                'min_stock_level': 200
            },
            {
                'unspsc_code': 'OT51102305',
                'name': '医用垃圾袋',
                'category': 'OT',
                'unit': '卷',
                'standard': '50个/卷',
                'shelf_life': 60,
                'storage_temp': '常温干燥',
                'is_controlled': False,
                'description': '用于医疗废物的收集和处理',
                'avg_price': 35.00,
                'min_stock_level': 300
            }
        ]

        # 创建医疗物资记录
        count = 0
        for data in supplies_data:
            # 随机选择一个供应商
            data['supplier'] = random.choice(suppliers)
            
            # 创建医疗物资记录
            medical_supply = MedicalSupply(**data)
            medical_supply.save()
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'成功导入 {count} 种医疗物资数据'))
