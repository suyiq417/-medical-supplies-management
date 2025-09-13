<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getSupplies } from '@/api/modules/index';
import { ElMessage } from 'element-plus';
import type { MedicalSupply } from '@/types/models';

const router = useRouter();
const supplies = ref<MedicalSupply[]>([]);
const loading = ref(true);
const total = ref(0);
const searchForm = reactive({
    name: '',
    category: '',
    is_controlled: ''
});

const categoryOptions = [
    { label: '药品', value: 'DG' },
    { label: '医疗设备', value: 'DV' },
    { label: '防护装备', value: 'PP' },
    { label: '检测试剂', value: 'RT' },
    { label: '一次性耗材', value: 'CS' },
    { label: '其他', value: 'OT' }
];

const pagination = reactive({
    currentPage: 1,
    pageSize: 10
});

// 获取物资列表
const fetchSupplies = async () => {
    loading.value = true;
    try {
        const params = {
            name: searchForm.name,
            category: searchForm.category,
            is_controlled: searchForm.is_controlled,
            page: pagination.currentPage,
            page_size: pagination.pageSize
        };

        const res = await getSupplies(params);
        if (res) {
            supplies.value = res.results || res;
            total.value = res.count || supplies.value.length;
        }
    } catch (err) {
        console.error('获取物资列表失败', err);
        ElMessage.error('获取物资列表失败');
    } finally {
        loading.value = false;
    }
};

// 搜索
const handleSearch = () => {
    pagination.currentPage = 1;
    fetchSupplies();
};

// 重置
const handleReset = () => {
    searchForm.name = '';
    searchForm.category = '';
    searchForm.is_controlled = '';
    pagination.currentPage = 1;
    fetchSupplies();
};

// 分页变化
const handlePageChange = (page: number) => {
    pagination.currentPage = page;
    fetchSupplies();
};

// 查看详情
const handleDetail = (supply: MedicalSupply) => {
    router.push(`/management/supplies/${supply.unspsc_code}`);
};

onMounted(() => {
    fetchSupplies();
});
</script>

<template>
    <div class="supply-container">
        <!-- 搜索表单 -->
        <div class="search-form">
            <el-form :model="searchForm" inline>
                <el-form-item label="物资名称">
                    <el-input v-model="searchForm.name" placeholder="请输入物资名称" clearable />
                </el-form-item>
                <el-form-item label="物资类型">
                    <el-select v-model="searchForm.category" placeholder="请选择物资类型" clearable>
                        <el-option v-for="item in categoryOptions" :key="item.value" :label="item.label"
                            :value="item.value" />
                    </el-select>
                </el-form-item>
                <el-form-item label="受控物资">
                    <el-select v-model="searchForm.is_controlled" placeholder="请选择" clearable>
                        <el-option label="是" value="true" />
                        <el-option label="否" value="false" />
                    </el-select>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleSearch">查询</el-button>
                    <el-button @click="handleReset">重置</el-button>
                </el-form-item>
            </el-form>
        </div>

        <!-- 物资列表 -->
        <div class="supply-list">
            <el-table v-loading="loading" :data="supplies" stripe style="width: 100%">
                <el-table-column prop="unspsc_code" label="UNSPSC编码" width="150" />
                <el-table-column prop="name" label="物资名称" show-overflow-tooltip />
                <el-table-column prop="category_display" label="物资类型" width="120" />
                <el-table-column prop="unit" label="计量单位" width="100" />
                <el-table-column prop="shelf_life" label="保质期(月)" width="120" align="center" />
                <el-table-column prop="storage_temp" label="存储温度" width="120" />
                <el-table-column label="受控物资" width="100" align="center">
                    <template #default="scope">
                        <el-tag :type="scope.row.is_controlled ? 'danger' : 'info'" size="small">
                            {{ scope.row.is_controlled ? '是' : '否' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="min_stock_level" label="最低库存" width="100" align="center" />
                <el-table-column label="操作" width="100" fixed="right" align="center">
                    <template #default="scope">
                        <el-button link type="primary" size="small" @click="handleDetail(scope.row)">查看</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination-container">
                <el-pagination v-model:currentPage="pagination.currentPage" :page-size="pagination.pageSize"
                    :total="total" layout="total, prev, pager, next, jumper" @current-change="handlePageChange"
                    background small />
            </div>
        </div>
    </div>
</template>

<style scoped lang="scss">
.supply-container {
    padding: 20px;

    .search-form {
        background: rgba(0, 20, 45, 0.7);
        border: 1px solid rgba(0, 180, 220, 0.3);
        border-radius: 4px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .supply-list {
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
}
</style>
