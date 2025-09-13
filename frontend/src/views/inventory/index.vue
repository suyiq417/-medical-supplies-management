<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getInventoryBatches, getHospitals, getSupplies } from '@/api/modules/index';
import { ElMessage } from 'element-plus';
import type { InventoryBatch, Hospital, MedicalSupply } from '@/types/models';

const router = useRouter();
const inventoryBatches = ref<InventoryBatch[]>([]);
const hospitals = ref<Hospital[]>([]);
const supplies = ref<MedicalSupply[]>([]);
const loading = ref(true);
const total = ref(0);

// 搜索表单
const searchForm = reactive({
    batch_number: '',
    hospital_id: '',
    supply_id: '',
    expiring_soon: false
});

// 分页配置
const pagination = reactive({
    currentPage: 1,
    pageSize: 10
});
// 获取数据
const fetchData = async () => {
    loading.value = true;
    try {
        const params = {
            batch_number: searchForm.batch_number,
            hospital_id: searchForm.hospital_id,
            supply_id: searchForm.supply_id,
            expiring_soon: searchForm.expiring_soon ? 'true' : '',
            page: pagination.currentPage,
            page_size: pagination.pageSize
        };

        const res = await getInventoryBatches(params);
        if (res) {
            inventoryBatches.value = res.results || res;
            total.value = res.count || inventoryBatches.value.length;
        }
    } catch (err) {
        console.error('获取库存批次失败', err);
        ElMessage.error('获取库存批次失败');
    } finally {
        loading.value = false;
    }
};

// 加载医院和物资下拉选项
const loadOptions = async () => {
    try {
        // 加载医院列表
        const hospitalRes = await getHospitals({ page_size: 100 });
        if (hospitalRes) {
            hospitals.value = hospitalRes.results || hospitalRes;
        }

        // 加载物资列表
        const supplyRes = await getSupplies({ page_size: 100 });
        if (supplyRes) {
            supplies.value = supplyRes.results || supplyRes;
        }
    } catch (err) {
        console.error('加载选项失败', err);
        ElMessage.warning('部分筛选选项加载失败');
    }
};

// 处理搜索
const handleSearch = () => {
    pagination.currentPage = 1;
    fetchData();
};

// 重置搜索
const handleReset = () => {
    searchForm.batch_number = '';
    searchForm.hospital_id = '';
    searchForm.supply_id = '';
    searchForm.expiring_soon = false;
    pagination.currentPage = 1;
    fetchData();
};

// 页码变化
const handlePageChange = (page: number) => {
    pagination.currentPage = page;
    fetchData();
};

// 查看详情
const handleDetail = (batch: InventoryBatch) => {
    router.push(`/management/inventory/${batch.batch_id}`);
};

// 查看医院
const handleViewHospital = (hospitalId: string) => {
    router.push(`/management/hospitals/${hospitalId}`);
};

// 查看物资
const handleViewSupply = (supplyCode: string) => {
    router.push(`/management/supplies/${supplyCode}`);
};

// 格式化日期
const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
};

onMounted(() => {
    fetchData();
    loadOptions();
});
</script>

<template>
    <div class="inventory-container">
        <!-- 搜索表单 -->
        <div class="search-form">
            <el-form :model="searchForm" inline>
                <el-form-item label="批次号">
                    <el-input v-model="searchForm.batch_number" placeholder="请输入批次号" clearable />
                </el-form-item>
                <el-form-item label="所属医院">
                    <el-select v-model="searchForm.hospital_id" placeholder="请选择医院" clearable filterable>
                        <el-option v-for="hospital in hospitals" :key="hospital.hospital_id" :label="hospital.name"
                            :value="hospital.hospital_id" />
                    </el-select>
                </el-form-item>
                <el-form-item label="物资类型">
                    <el-select v-model="searchForm.supply_id" placeholder="请选择物资" clearable filterable>
                        <el-option v-for="supply in supplies" :key="supply.unspsc_code" :label="supply.name"
                            :value="supply.unspsc_code" />
                    </el-select>
                </el-form-item>
                <el-form-item label="即将过期">
                    <el-switch v-model="searchForm.expiring_soon" />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleSearch">查询</el-button>
                    <el-button @click="handleReset">重置</el-button>
                </el-form-item>
            </el-form>
        </div>

        <!-- 库存列表 -->
        <div class="inventory-list">
            <el-table v-loading="loading" :data="inventoryBatches" border stripe style="width: 100%">
                <el-table-column prop="batch_number" label="批次号" width="150" />
                <el-table-column label="所属医院" width="200">
                    <template #default="scope">
                        <el-button v-if="scope.row.hospital" link type="primary"
                            @click="handleViewHospital(scope.row.hospital.hospital_id)">
                            {{ scope.row.hospital.name }}
                        </el-button>
                        <span v-else>-</span>
                    </template>
                </el-table-column>
                <el-table-column label="物资名称">
                    <template #default="scope">
                        <el-button v-if="scope.row.supply" link type="primary"
                            @click="handleViewSupply(scope.row.supply.unspsc_code)">
                            {{ scope.row.supply.name }}
                        </el-button>
                        <span v-else>-</span>
                    </template>
                </el-table-column>
                <el-table-column label="物资类型" width="120">
                    <template #default="scope">
                        {{ scope.row.supply?.category_display || '-' }}
                    </template>
                </el-table-column>
                <el-table-column prop="quantity" label="数量" width="100" />
                <el-table-column label="生产日期" width="120">
                    <template #default="scope">
                        {{ formatDate(scope.row.production_date) }}
                    </template>
                </el-table-column>
                <el-table-column label="过期日期" width="120">
                    <template #default="scope">
                        <span
                            :class="{ 'text-danger': scope.row.expiration_date && new Date(scope.row.expiration_date) <= new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) }">
                            {{ formatDate(scope.row.expiration_date) }}
                        </span>
                    </template>
                </el-table-column>
                <el-table-column label="入库日期" width="120">
                    <template #default="scope">
                        {{ formatDate(scope.row.received_date) }}
                    </template>
                </el-table-column>
                <el-table-column label="质检状态" width="100">
                    <template #default="scope">
                        <el-tag :type="scope.row.quality_check_passed ? 'success' : 'danger'">
                            {{ scope.row.quality_check_passed ? '通过' : '未通过' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="120">
                    <template #default="scope">
                        <el-button link type="primary" size="small" @click="handleDetail(scope.row)">查看详情</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination-container">
                <el-pagination v-model:currentPage="pagination.currentPage" :page-size="pagination.pageSize"
                    :total="total" layout="total, prev, pager, next, jumper" @current-change="handlePageChange" />
            </div>
        </div>
    </div>
</template>

<style scoped lang="scss">
.inventory-container {
    padding: 20px;

    .search-form {
        background: rgba(0, 20, 45, 0.7);
        border: 1px solid rgba(0, 180, 220, 0.3);
        border-radius: 4px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .inventory-list {
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

    .text-danger {
        color: #F56C6C;
    }
}
</style>
