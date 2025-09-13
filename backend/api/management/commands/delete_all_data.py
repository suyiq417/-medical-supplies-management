from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connection
class Command(BaseCommand):
    help = '删除数据库中所有应用的所有数据。警告：此操作不可逆！'

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', '--no-input', action='store_true',
            help='在不要求确认的情况下删除所有数据。',
        )

    def handle(self, *args, **options):
        confirm = options['noinput']  # 修改这里，将 'no_input' 改为 'noinput'
        if not confirm:
            confirm = input(
                "警告！此操作将删除数据库中的所有数据。\n"
                "您确定要继续吗？ [yes/N]: "
            )

        if confirm.lower() == 'yes':
            self.stdout.write(self.style.WARNING('开始删除所有数据...'))

            # 获取所有已注册的模型
            all_models = apps.get_models()

            # 禁用外键约束 (根据数据库类型可能需要调整)
            # 注意：这部分代码可能需要根据您使用的具体数据库进行调整
            # 例如，对于 PostgreSQL，可能是 SET CONSTRAINTS ALL DEFERRED;
            # 对于 MySQL，可能是 SET FOREIGN_KEY_CHECKS = 0;
            # 对于 SQLite，外键默认可能不强制执行，或者需要 PRAGMA foreign_keys = OFF;
            cursor = connection.cursor()
            db_vendor = connection.vendor
            try:
                if db_vendor == 'mysql':
                    cursor.execute('SET FOREIGN_KEY_CHECKS = 0;')
                    self.stdout.write(self.style.NOTICE('已禁用 MySQL 外键检查。'))
                elif db_vendor == 'postgresql':
                    # PostgreSQL 通常不需要显式禁用，TRUNCATE CASCADE 可以处理
                    pass
                elif db_vendor == 'sqlite':
                    cursor.execute('PRAGMA foreign_keys = OFF;')
                    self.stdout.write(self.style.NOTICE('已禁用 SQLite 外键检查。'))

                # 按特定顺序删除或使用 TRUNCATE (如果数据库支持)
                # 更安全的方式是按依赖关系逆序删除，或者使用 TRUNCATE
                # 这里使用简单的 delete()，对于复杂依赖可能失败
                # 更好的方法是使用 TRUNCATE (如果数据库支持且需要快速清空)
                # 例如 PostgreSQL: cursor.execute(f'TRUNCATE TABLE {model._meta.db_table} RESTART IDENTITY CASCADE;')
                # 例如 MySQL: cursor.execute(f'TRUNCATE TABLE `{model._meta.db_table}`;')

                # 尝试按顺序删除，先删除依赖模型
                # 注意：这个顺序需要根据你的实际模型依赖关系调整
                ordered_models = [
                    # 先删除关联和依赖较多的模型
                    apps.get_model('api', 'ItemFulfillment'),
                    apps.get_model('api', 'RequestItem'), # <--- 修改这里
                    apps.get_model('api', 'InventoryAlert'),
                    apps.get_model('api', 'SupplyRequest'),
                    apps.get_model('api', 'InventoryBatch'),
                    # 再删除基础表
                    apps.get_model('api', 'MedicalSupply'), # <--- 修改这里，原为 Supply
                    apps.get_model('api', 'Hospital'),
                    apps.get_model('api', 'Supplier'),
                    # 如果需要删除用户，可以取消下一行的注释
                    # apps.get_model('auth', 'User'),
                    # 其他模型...
                ]

                # 获取所有模型的列表，排除已经手动排序的和 Django 内部模型
                # 调整这里的过滤条件，确保 auth 应用中的 User/Group 可以被包含（如果需要删除）
                excluded_apps = ['contenttypes', 'sessions', 'admin']
                # 如果不需要删除 User/Group，也加入 'auth'
                # excluded_apps.append('auth')

                remaining_models = [
                    m for m in all_models
                    if m not in ordered_models and m._meta.app_label not in excluded_apps
                ]
                # 如果需要删除 User/Group 但它们不在 ordered_models 中，确保它们被包含
                # 例如，如果上面注释了 User，这里可以添加：
                # auth_models_to_delete = [apps.get_model('auth', 'User'), apps.get_model('auth', 'Group')]
                # remaining_models.extend([m for m in auth_models_to_delete if m not in ordered_models and m not in remaining_models])


                # 合并列表，确保手动排序的模型在前面
                final_model_order = ordered_models + remaining_models


                for model in final_model_order:
                    # 跳过 Django 内部模型 (如果上面没有过滤掉 auth，这里需要更精确的判断)
                    # if model._meta.app_label in ['admin', 'contenttypes', 'sessions']:
                    #     continue
                    # if model._meta.app_label == 'auth' and model._meta.object_name not in ['User', 'Group']: # 如果保留 User/Group
                    #      continue

                    try:
                        count, _ = model._base_manager.all().delete()
                        if count > 0:
                            self.stdout.write(f'删除了 {count} 条 {model._meta.verbose_name_plural} 数据')
                    except Exception as e:
                         self.stdout.write(self.style.ERROR(f'删除 {model._meta.verbose_name_plural} 时出错: {e}'))


            finally:
                # 重新启用外键约束
                if db_vendor == 'mysql':
                    cursor.execute('SET FOREIGN_KEY_CHECKS = 1;')
                    self.stdout.write(self.style.NOTICE('已重新启用 MySQL 外键检查。'))
                elif db_vendor == 'postgresql':
                    pass # 通常不需要
                elif db_vendor == 'sqlite':
                    cursor.execute('PRAGMA foreign_keys = ON;')
                    self.stdout.write(self.style.NOTICE('已重新启用 SQLite 外键检查。'))
                cursor.close()

            self.stdout.write(self.style.SUCCESS('成功删除所有数据。'))
        else:
            self.stdout.write(self.style.ERROR('操作已取消。'))
