<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { getSuppliers } from '@/api/modules/index';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { Supplier } from '@/types/models';

// 扩展 Supplier 类型以允许 contact_info 是字符串或对象
interface ProcessedSupplier extends Omit<Supplier, 'contact_info'> {
    contact_info: Record<string, any> | null | string; // 允许是对象、null 或原始字符串
}

const suppliers = ref<ProcessedSupplier[]>([]); // 使用扩展后的类型
const loading = ref(true);
const total = ref(0);

// 搜索表单
const searchForm = reactive({
    name: '',
    contact_person: ''
});

// 分页配置
const pagination = reactive({
    currentPage: 1,
    pageSize: 10
});

// 获取供应商列表
const fetchSuppliers = async () => {
    loading.value = true;
    try {
        const params = {
            name: searchForm.name,
            contact_person: searchForm.contact_person,
            page: pagination.currentPage,
            page_size: pagination.pageSize
        };

        const res = await getSuppliers(params);
        if (res) {
            let results: ProcessedSupplier[] = res.results || res; // 假设 res.results 是数组

            // --- 新增：解析 contact_info ---
            results = results.map(supplier => {
                if (supplier.contact_info && typeof supplier.contact_info === 'string') {
                    try {
                        // 尝试解析 JSON 字符串
                        supplier.contact_info = JSON.parse(supplier.contact_info);
                    } catch (e) {
                        console.error('解析 contact_info 失败:', supplier.supplier_id, e);
                        // 解析失败，可以将其设为 null 或保留原始字符串，或设置默认值
                        supplier.contact_info = null; // 或者 {}
                    }
                }
                return supplier;
            });
            // --- 解析结束 ---

            suppliers.value = results;
            total.value = res.count || suppliers.value.length;
        }
    } catch (err) {
        console.error('获取供应商列表失败', err);
        ElMessage.error('获取供应商列表失败');
    } finally {
        loading.value = false;
    }
};

// 搜索
const handleSearch = () => {
    pagination.currentPage = 1;
    fetchSuppliers();
};

// 重置
const handleReset = () => {
    searchForm.name = '';
    searchForm.contact_person = '';
    pagination.currentPage = 1;
    fetchSuppliers();
};

// 分页变化
const handlePageChange = (page: number) => {
    pagination.currentPage = page;
    fetchSuppliers();
};

// 查看供应商详情 - 使用抽屉形式展示
const detailDrawerVisible = ref(false);
// currentSupplier 的类型也需要更新，或者在使用时确保 contact_info 是对象
const currentSupplier = ref<ProcessedSupplier | null>(null);

const showSupplierDetail = (supplier: ProcessedSupplier) => { // 参数类型更新
    // 确保传递给抽屉的 contact_info 是对象 (如果尚未解析)
    if (supplier.contact_info && typeof supplier.contact_info === 'string') {
        try {
            supplier.contact_info = JSON.parse(supplier.contact_info);
        } catch (e) {
            console.error('详情解析 contact_info 失败:', supplier.supplier_id, e);
            supplier.contact_info = null;
        }
    }
    currentSupplier.value = supplier;
    detailDrawerVisible.value = true;
};

// 格式化信用等级星星
const formatCreditRating = (rating: number) => {
    return '★'.repeat(rating) + '☆'.repeat(5 - rating);
};

onMounted(() => {
    fetchSuppliers();
});
</script>

<template>
    <div class="supplier-container">
        <!-- 搜索表单 -->
        <div class="search-form">
            <el-form :model="searchForm" inline>
                <el-form-item label="供应商名称">
                    <el-input v-model="searchForm.name" placeholder="请输入供应商名称" clearable />
                </el-form-item>
                <el-form-item label="联系人">
                    <el-input v-model="searchForm.contact_person" placeholder="请输入联系人姓名" clearable />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleSearch">查询</el-button>
                    <el-button @click="handleReset">重置</el-button>
                </el-form-item>
            </el-form>
        </div>

        <!-- 供应商列表 -->
        <div class="supplier-list">
            <el-table v-loading="loading" :data="suppliers" stripe style="width: 100%">
                <el-table-column prop="name" label="供应商名称" min-width="180" show-overflow-tooltip />
                <el-table-column prop="contact_person" label="联系人" width="120" />
                <el-table-column label="联系电话" width="150">
                    <template #default="scope">
                        {{ scope.row.contact_info?.phone || '-' }}
                    </template>
                </el-table-column>
                <el-table-column label="电子邮箱" width="180">
                    <template #default="scope">
                        {{ scope.row.contact_info?.email || '-' }}
                    </template>
                </el-table-column>
                <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
                <el-table-column label="信用评级" width="120">
                    <template #default="scope">
                        <span
                            :style="{ color: scope.row.credit_rating > 3 ? '#67C23A' : scope.row.credit_rating > 1 ? '#E6A23C' : '#F56C6C' }">
                            {{ formatCreditRating(scope.row.credit_rating) }}
                        </span>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                    <template #default="scope">
                        <el-button link type="primary" size="small"
                            @click="showSupplierDetail(scope.row)">详情</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination-container">
                <el-pagination v-model:currentPage="pagination.currentPage" :page-size="pagination.pageSize"
                    :total="total" layout="total, prev, pager, next, jumper" @current-change="handlePageChange" />
            </div>
        </div>

        <!-- 供应商详情抽屉 -->
        <el-drawer v-model="detailDrawerVisible" title="供应商详情" size="50%" direction="rtl" :with-header="true"
            :destroy-on-close="true">
            <!-- 确保 currentSupplier.contact_info 在模板中也被正确处理 -->
            <div v-if="currentSupplier" class="supplier-detail">
                <div class="detail-header">
                    <h2>{{ currentSupplier.name }}</h2>
                    <div class="credit-rating">
                        <span>信用评级: </span>
                        <span
                            :style="{ color: currentSupplier.credit_rating > 3 ? '#67C23A' : currentSupplier.credit_rating > 1 ? '#E6A23C' : '#F56C6C' }">
                            {{ formatCreditRating(currentSupplier.credit_rating) }}
                        </span>
                    </div>
                </div>

                <el-divider />

                <div class="detail-section">
                    <h3>基本信息</h3>
                    <div class="detail-item">
                        <span class="item-label">联系人:</span>
                        <span class="item-value">{{ currentSupplier.contact_person }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="item-label">联系电话:</span>
                        <!-- 模板中的访问方式不变，因为数据已被处理成对象 -->
                        <span class="item-value">{{ currentSupplier.contact_info?.phone || '-' }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="item-label">电子邮箱:</span>
                        <span class="item-value">{{ currentSupplier.contact_info?.email || '-' }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="item-label">地址:</span>
                        <span class="item-value">{{ currentSupplier.address }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="item-label">创建时间:</span>
                        <span class="item-value">{{ new Date(currentSupplier.created_at).toLocaleString() }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="item-label">更新时间:</span>
                        <span class="item-value">{{ new Date(currentSupplier.updated_at).toLocaleString() }}</span>
                    </div>
                </div>

                <div v-if="currentSupplier.contact_info && typeof currentSupplier.contact_info === 'object' && currentSupplier.contact_info.additional_contacts"
                    class="detail-section">
                    <h3>其他联系人</h3>
                    <!-- 确保这里访问的是解析后的对象 -->
                    <div v-for="(contact, index) in currentSupplier.contact_info.additional_contacts" :key="index"
                        class="contact-card">
                        <div class="detail-item">
                            <span class="item-label">姓名:</span>
                            <span class="item-value">{{ contact.name }}</span>
                        </div>
                        <div class="detail-item">
                            <span class="item-label">职位:</span>
                            <span class="item-value">{{ contact.position }}</span>
                        </div>
                        <div class="detail-item">
                            <span class="item-label">电话:</span>
                            <span class="item-value">{{ contact.phone }}</span>
                        </div>
                        <div class="detail-item">
                            <span class="item-label">邮箱:</span>
                            <span class="item-value">{{ contact.email }}</span>
                        </div>
                    </div>
                </div>

                <div v-if="currentSupplier.contact_info && typeof currentSupplier.contact_info === 'object' && currentSupplier.contact_info.remarks"
                    class="detail-section">
                    <h3>备注</h3>
                    <div class="remarks">{{ currentSupplier.contact_info.remarks }}</div>
                </div>
            </div>
        </el-drawer>
    </div>
</template>

<style scoped lang="scss">
.supplier-container {
    padding: 20px;

    .search-form {
        background: rgba(0, 20, 45, 0.7);
        border: 1px solid rgba(0, 180, 220, 0.3);
        border-radius: 4px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .supplier-list {
        background: rgba(0, 20, 45, 0.7);
        border: 1px solid rgba(0, 180, 220, 0.3);
        border-radius: 4px;
        padding: 20px;

        .pagination-container {
            margin-top: 20px;
            display: flex;
            justify-content: flex-end;
        }
    }

    // --- 新增：抽屉样式调整 ---
    :deep(.el-drawer) {
        // 抽屉背景
        background-color: #030c1a !important; // 深蓝背景，可根据你的主题调整
        border-left: 1px solid rgba(0, 180, 220, 0.3); // 左侧边框

        .el-drawer__header {
            color: #00fdfa; // 标题颜色 - 主题亮色
            margin-bottom: 0; // 移除默认的 margin
            padding: 15px 20px;
            border-bottom: 1px solid rgba(0, 180, 220, 0.2); // 头部下边框
            box-sizing: border-box;

            .el-drawer__title {
                font-size: 18px;
            }

            .el-drawer__close-btn {
                color: #a0cfff; // 关闭按钮颜色

                &:hover {
                    color: #00fdfa;
                }
            }
        }

        .el-drawer__body {
            padding: 0; // 移除默认 padding，由内部 .supplier-detail 控制
            color: rgba(255, 255, 255, 0.85); // 默认文字颜色
        }
    }

    .supplier-detail {
        padding: 20px; // 内部内容区域的 padding
        height: 100%;
        overflow-y: auto; // 使内容可滚动

        .detail-header {
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px dashed rgba(0, 180, 220, 0.2); // 虚线分隔

            h2 {
                margin: 0 0 10px 0;
                color: #00fdfa; // 供应商名称颜色
                font-size: 20px;
            }

            .credit-rating {
                font-size: 16px;
                color: rgba(255, 255, 255, 0.8);

                span:first-child {
                    color: rgba(255, 255, 255, 0.7);
                    margin-right: 5px;
                }
            }
        }

        .el-divider--horizontal {
            margin: 20px 0;
            background: none; // 移除默认背景
            border-top: 1px solid rgba(0, 180, 220, 0.2); // 分割线颜色
        }

        .detail-section {
            margin-bottom: 25px;

            h3 {
                color: #00fdfa; // Section 标题颜色
                margin-bottom: 15px;
                font-size: 16px;
                border-left: 3px solid #00fdfa;
                padding-left: 10px;
            }

            .detail-item {
                display: flex;
                margin-bottom: 12px;
                font-size: 14px;
                line-height: 1.6;

                .item-label {
                    width: 100px;
                    color: rgba(255, 255, 255, 0.6); // 标签颜色调暗
                    flex-shrink: 0;
                    text-align: right; // 右对齐标签
                    margin-right: 15px; // 增加标签和值之间的距离
                }

                .item-value {
                    flex: 1;
                    color: rgba(255, 255, 255, 0.9); // 值颜色
                    word-break: break-all; // 防止长内容溢出
                }
            }

            .contact-card {
                background: rgba(0, 30, 60, 0.4); // 卡片背景色
                border: 1px solid rgba(0, 180, 220, 0.2); // 卡片边框
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 15px;

                .detail-item {
                    margin-bottom: 8px; // 调整卡片内间距

                    &:last-child {
                        margin-bottom: 0;
                    }
                }
            }

            .remarks {
                white-space: pre-line;
                line-height: 1.7;
                color: rgba(255, 255, 255, 0.8);
                background: rgba(0, 30, 60, 0.2); // 备注区域背景
                padding: 10px 15px;
                border-radius: 4px;
                border: 1px solid rgba(0, 180, 220, 0.1);
            }
        }
    }

    // --- 抽屉样式调整结束 ---
}
</style>
