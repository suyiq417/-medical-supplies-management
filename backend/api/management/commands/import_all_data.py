from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = '按照正确的顺序导入所有数据'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('开始导入医疗物资管理系统的所有数据...'))
        
        # 1. 导入医院数据
        self.stdout.write(self.style.NOTICE('导入医院数据...'))
        call_command('import_hospitals')
        
        # 2. 导入供应商数据
        self.stdout.write(self.style.NOTICE('导入供应商数据...'))
        call_command('import_suppliers')
        
        # 3. 导入医疗物资数据
        self.stdout.write(self.style.NOTICE('导入医疗物资数据...'))
        call_command('import_supplies')
        
        # 4. 导入库存批次数据
        self.stdout.write(self.style.NOTICE('导入库存批次数据...'))
        call_command('import_inventory')
        
        # 5. 导入物资请求数据
        self.stdout.write(self.style.NOTICE('导入物资请求数据...'))
        call_command('import_requests')
        
        # 6. 导入物资分配记录数据
        self.stdout.write(self.style.NOTICE('导入物资分配记录数据...'))
        call_command('import_fulfillments')
        
        # 7. 导入库存预警数据
        self.stdout.write(self.style.NOTICE('导入库存预警数据...'))
        call_command('import_alerts')
        
        self.stdout.write(self.style.SUCCESS('所有数据导入完成！'))
