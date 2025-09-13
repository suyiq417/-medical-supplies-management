<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { getRequestItemsForAllocation, getHospitals, getSupplies, updateRequestItemAllocation } from '@/api/modules/index';
import { ElMessage, ElInputNumber } from 'element-plus';
import type { RequestItemAllocationData, Hospital, MedicalSupply } from '@/types/models';
import { EditPen } from '@element-plus/icons-vue';

const router = useRouter();
const requestItems = ref<RequestItemAllocationData[]>([]);
const hospitals = ref<Hospital[]>([]);
const supplies = ref<MedicalSupply[]>([]);
const loading = ref(false);
const total = ref(0);

const searchForm = reactive({
    supply_code: '',
    hospital_id: '',
    emergency: '',
    start_date: '',
    end_date: '',
});

const sortState = reactive({
    prop: 'request.priority',
    order: 'descending',
});

const pagination = reactive({
    currentPage: 1,
    pageSize: 10,
});

const supplySelected = computed(() => !!searchForm.supply_code);

const fetchRequestItems = async () => {
    if (!supplySelected.value) {
        requestItems.value = [];
        total.value = 0;
        loading.value = false;
        return;
    }
    loading.value = true;
    try {
        let ordering = '';
        if (sortState.prop) {
            ordering = sortState.order === 'descending' ? `-${sortState.prop}` : sortState.prop;
        }

        const params = {
            supply_code: searchForm.supply_code,
            request__hospital_id: searchForm.hospital_id,
            request__emergency: searchForm.emergency,
            request__required_by__gte: searchForm.start_date,
            request__required_by__lte: searchForm.end_date,
            ordering: ordering,
            page: pagination.currentPage,
            page_size: pagination.pageSize,
        };

        const filteredParams = Object.entries(params).reduce((acc, [key, value]) => {
            if (value !== null && value !== '' && value !== undefined) {
                acc[key] = value;
            }
            return acc;
        }, {} as Record<string, any>);

        const res = await getRequestItemsForAllocation(filteredParams);
        if (res) {
            requestItems.value = res.results || [];
            total.value = res.count || requestItems.value.length;
        } else {
            requestItems.value = [];
            total.value = 0;
        }
    } catch (err) {
        console.error('获取待分配物资项列表失败', err);
        ElMessage.error('获取待分配物资项列表失败');
        requestItems.value = [];
        total.value = 0;
    } finally {
        loading.value = false;
    }
};

const loadHospitals = async () => {
    try {
        const res = await getHospitals({ page_size: 100 });
        if (res) {
            hospitals.value = res.results || res;
        }
    } catch (err) {
        console.error('加载医院列表失败', err);
        ElMessage.warning('医院列表加载失败');
    }
};

const loadSupplies = async () => {
    try {
        const res = await getSupplies({ page_size: 200 });
        if (res) {
            supplies.value = res.results || res;
        }
    } catch (err) {
        console.error('加载物资列表失败', err);
    }
};

const handleSearch = () => {
    pagination.currentPage = 1;
    fetchRequestItems();
};

const handleReset = () => {
    searchForm.supply_code = '';
    searchForm.hospital_id = '';
    searchForm.emergency = '';
    searchForm.start_date = '';
    searchForm.end_date = '';
    sortState.prop = 'request.priority';
    sortState.order = 'descending';
    pagination.currentPage = 1;
    requestItems.value = [];
    total.value = 0;
};

const handlePageChange = (page: number) => {
    pagination.currentPage = page;
    fetchRequestItems();
};

const handleSortChange = ({ prop, order }: { prop: string, order: 'ascending' | 'descending' | null }) => {
    sortState.prop = order ? prop : 'request.priority';
    sortState.order = order || 'descending';
    pagination.currentPage = 1;
    fetchRequestItems();
};

const handleDetail = (item: RequestItemAllocationData) => {
    if (item.request?.request_id) {
        router.push(`/management/requests/${item.request.request_id}`);
    } else {
        ElMessage.warning('无法获取原请求ID');
    }
};

const editingAllocation = reactive<Record<string, number | null>>({});

const startEditAllocation = (item: RequestItemAllocationData) => {
    if (item && item.item_id !== undefined) {
        if (item.request?.status !== 'AP' && item.request?.status !== 'SB') {
            ElMessage.warning('只有已批准的请求才能分配！');
            return;
        }
        editingAllocation[item.item_id] = item.allocated ?? 0;
    }
};

const cancelEditAllocation = (itemId: string) => {
    delete editingAllocation[itemId];
};

const saveItemAllocation = async (item: RequestItemAllocationData) => {
    if (!item || item.item_id === undefined || editingAllocation[item.item_id] === undefined) {
        return;
    }
    const newAllocatedQuantity = editingAllocation[item.item_id];

    if (newAllocatedQuantity === null || newAllocatedQuantity < 0) {
        ElMessage.warning('分配数量不能为空或负数');
        return;
    }
    if (newAllocatedQuantity > item.quantity) {
        ElMessage.warning(`分配数量 (${newAllocatedQuantity}) 不能超过请求数量 ${item.quantity}`);
        return;
    }
    if (newAllocatedQuantity === item.allocated) {
        delete editingAllocation[item.item_id];
        ElMessage.info('分配数量未改变');
        return;
    }

    try {
        await updateRequestItemAllocation(item.request.request_id, item.item_id, newAllocatedQuantity);
        ElMessage.success('分配成功');
        delete editingAllocation[item.item_id];
        fetchRequestItems();
    } catch (error: any) {
        console.error('分配失败', error);
        const errorMsg = error?.detail || error?.error || error?.message || '分配失败';
        ElMessage.error(errorMsg);
    }
};

const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return '-';
    try {
        return new Date(dateStr).toLocaleDateString();
    } catch (e) {
        return dateStr;
    }
};

watch(() => searchForm.supply_code, (newVal, oldVal) => {
    if (newVal !== oldVal) {
        handleSearch();
    }
});

onMounted(() => {
    loadHospitals();
    loadSupplies();
});
</script>

<template>
    <div class="request-container">
        <div class="search-form">
            <el-form :model="searchForm" inline>
                <el-form-item label="选择物资进行调度" prop="supply_code" required>
                    <el-select v-model="searchForm.supply_code" placeholder="请选择物资种类" clearable filterable
                        style="width: 250px;">
                        <el-option v-for="supply in supplies" :key="supply.unspsc_code" :label="supply.name"
                            :value="supply.unspsc_code" />
                    </el-select>
                </el-form-item>

                <el-form-item label="医院" v-if="supplySelected">
                    <el-select v-model="searchForm.hospital_id" placeholder="筛选医院" clearable filterable>
                        <el-option v-for="hospital in hospitals" :key="hospital.hospital_id" :label="hospital.name"
                            :value="hospital.hospital_id" />
                    </el-select>
                </el-form-item>
                <el-form-item label="紧急请求" v-if="supplySelected">
                    <el-select v-model="searchForm.emergency" placeholder="筛选紧急度" clearable>
                        <el-option label="是" value="true" />
                        <el-option label="否" value="false" />
                    </el-select>
                </el-form-item>
                <el-form-item label="需求日期范围" v-if="supplySelected">
                    <el-date-picker v-model="searchForm.start_date" type="date" placeholder="开始日期" style="width: 150px"
                        format="YYYY-MM-DD" value-format="YYYY-MM-DD" />
                    <span style="margin: 0 5px;">至</span>
                    <el-date-picker v-model="searchForm.end_date" type="date" placeholder="结束日期" style="width: 150px"
                        format="YYYY-MM-DD" value-format="YYYY-MM-DD" />
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" @click="handleSearch" :disabled="!supplySelected">查询</el-button>
                    <el-button @click="handleReset">重置</el-button>
                </el-form-item>
                <el-alert v-if="!supplySelected" title="请先选择物资种类以查看待分配项" type="info" show-icon :closable="false" />
            </el-form>
        </div>

        <div class="request-list">
            <el-table v-loading="loading" :data="requestItems" stripe style="width: 100%"
                @sort-change="handleSortChange" :default-sort="{ prop: 'request.priority', order: 'descending' }"
                empty-text="请先选择物资种类，或当前物资无待分配项">
                <el-table-column label="请求医院" prop="request.hospital.name" min-width="180" show-overflow-tooltip />
                <el-table-column label="请求优先级" prop="request.priority" width="120" sortable="custom" align="center">
                    <template #default="scope">
                        {{ scope.row.request?.priority?.toFixed(6) ?? '-' }}
                    </template>
                </el-table-column>
                <el-table-column label="需求时间" prop="request.required_by" width="120" sortable="custom">
                    <template #default="scope">
                        {{ formatDate(scope.row.request?.required_by) }}
                    </template>
                </el-table-column>
                <el-table-column label="紧急" prop="request.emergency" width="80" sortable="custom">
                    <template #default="scope">
                        <el-tag v-if="scope.row.request?.emergency === true" type="danger">是</el-tag>
                        <el-tag v-else type="info">否</el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="请求数量" prop="quantity" width="120" align="right">
                    <template #default="scope">
                        {{ scope.row.quantity }} {{ scope.row.supply?.unit }}
                    </template>
                </el-table-column>
                <el-table-column label="已分配" prop="allocated" width="120" align="right">
                    <template #default="scope">
                        {{ scope.row.allocated ?? 0 }} {{ scope.row.supply?.unit }}
                    </template>
                </el-table-column>
                <el-table-column label="待分配" width="120" align="right">
                    <template #default="scope">
                        <span
                            :style="{ color: (scope.row.quantity ?? 0) - (scope.row.allocated ?? 0) > 0 ? 'red' : 'inherit' }">
                            {{ (scope.row.quantity ?? 0) - (scope.row.allocated ?? 0) }} {{ scope.row.supply?.unit }}
                        </span>
                    </template>
                </el-table-column>
                <el-table-column prop="notes" label="物资备注" min-width="150" show-overflow-tooltip />
                <el-table-column label="操作" width="200" fixed="right">
                    <template #default="scope">
                        <div v-if="editingAllocation[scope.row.item_id] !== undefined"
                            style="display: flex; align-items: center; gap: 5px;">
                            <el-input-number v-model="editingAllocation[scope.row.item_id]" :min="0"
                                :max="scope.row.quantity" :step="1" size="small" controls-position="right"
                                style="width: 100px;" placeholder="数量" />
                            <el-button link type="primary" size="small"
                                @click="saveItemAllocation(scope.row)">保存</el-button>
                            <el-button link type="info" size="small"
                                @click="cancelEditAllocation(scope.row.item_id)">取消</el-button>
                        </div>
                        <el-button v-else link type="primary" size="small" :icon="EditPen"
                            @click="startEditAllocation(scope.row)">
                            分配
                        </el-button>
                        <el-button link type="info" size="small" @click="handleDetail(scope.row)">查看原请求</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <div class="pagination-container" v-if="supplySelected && total > 0">
                <el-pagination v-model:currentPage="pagination.currentPage" :page-size="pagination.pageSize"
                    :total="total" layout="total, prev, pager, next, jumper" @current-change="handlePageChange" />
            </div>
        </div>
    </div>
</template>

<style scoped lang="scss">
.request-container {
    padding: 20px;

    .search-form {
        background: rgba(0, 20, 45, 0.7);
        border: 1px solid rgba(0, 180, 220, 0.3);
        border-radius: 4px;
        padding: 20px;
        margin-bottom: 20px;

        .el-form--inline .el-form-item {
            margin-right: 15px;
            margin-bottom: 15px;
        }

        .el-alert {
            margin-top: 10px;
        }
    }

    .request-list {
        background: rgba(0, 20, 45, 0.7);
        border: 1px solid rgba(0, 180, 220, 0.3);
        border-radius: 4px;
        padding: 20px;

        .pagination-container {
            margin-top: 20px;
            display: flex;
            justify-content: flex-end;
        }

        .el-table .el-button+.el-button {
            margin-left: 8px;
        }
    }
}
</style>
