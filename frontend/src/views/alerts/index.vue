<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getInventoryAlertsList, getHospitals, resolveAlertById } from '@/api/modules/index';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { InventoryAlert, Hospital } from '@/types/models';

const router = useRouter();
const alerts = ref<InventoryAlert[]>([]);
const hospitals = ref<Hospital[]>([]);
const loading = ref(true);
const total = ref(0);

// 搜索表单
const searchForm = reactive({
    hospital_id: '',
    alert_type: '',
    is_resolved: '',
    start_date: '',
    end_date: ''
});

// 预警类型选项
const alertTypeOptions = [
    { value: 'LS', label: '低库存' },
    { value: 'EX', label: '过期预警' },
    { value: 'ED', label: '已过期' },
    { value: 'CP', label: '容量预警' }
];

// 分页配置
const pagination = reactive({
    currentPage: 1,
    pageSize: 10
});

// 获取预警列表
const fetchAlerts = async () => {
    loading.value = true;
    try {
        const params = {
            hospital_id: searchForm.hospital_id,
            alert_type: searchForm.alert_type,
            is_resolved: searchForm.is_resolved,
            created_at_start: searchForm.start_date,
            created_at_end: searchForm.end_date,
            page: pagination.currentPage,
            page_size: pagination.pageSize
        };

        const res = await getInventoryAlertsList(params);
        if (res) {
            alerts.value = res.results || res;
            total.value = res.count || alerts.value.length;
        }
    } catch (err) {
        console.error('获取预警列表失败', err);
        ElMessage.error('获取预警列表失败');
    } finally {
        loading.value = false;
    }
};

// 加载医院选项
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

// 搜索
const handleSearch = () => {
    pagination.currentPage = 1;
    fetchAlerts();
};

// 重置
const handleReset = () => {
    searchForm.hospital_id = '';
    searchForm.alert_type = '';
    searchForm.is_resolved = '';
    searchForm.start_date = '';
    searchForm.end_date = '';
    pagination.currentPage = 1;
    fetchAlerts();
};

// 页码变化
const handlePageChange = (page: number) => {
    pagination.currentPage = page;
    fetchAlerts();
};

// 查看详情
const handleDetail = (alert: InventoryAlert) => {
    router.push(`/management/alerts/${alert.alert_id}`);
};

// 解决预警
const handleResolveAlert = async (alert: InventoryAlert) => {
    try {
        await ElMessageBox.confirm('确认将此预警标记为已解决吗？', '确认解决', {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            type: 'warning'
        });

        const res = await resolveAlertById(alert.alert_id);
        if (res) {
            ElMessage.success('预警已标记为已解决');
            fetchAlerts();
        } else {
            ElMessage.error('预警解决失败');
        }
    } catch (err) {
        if (err !== 'cancel') {
            console.error('解决预警失败', err);
        }
    }
};

// 查看医院
const viewHospital = (hospitalId: string) => {
    router.push(`/management/hospitals/${hospitalId}`);
};

// 获取预警类型样式
const getAlertTypeClass = (type: string): 'success' | 'warning' | 'info' | 'danger' => {
    switch (type) {
        case 'LS': return 'warning';
        case 'EX': return 'info';
        case 'ED': return 'danger';
        case 'CP': return 'success';
        default: return 'info';
    }
};

// 格式化日期
const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
};

onMounted(() => {
    fetchAlerts();
    loadHospitals();
});
</script>

<template>
    <div class="alert-container">
        <!-- 搜索表单 -->
        <div class="search-form">
            <el-form :model="searchForm" inline>
                <el-form-item label="医院">
                    <el-select v-model="searchForm.hospital_id" placeholder="请选择医院" clearable filterable>
                        <el-option v-for="hospital in hospitals" :key="hospital.hospital_id" :label="hospital.name"
                            :value="hospital.hospital_id" />
                    </el-select>
                </el-form-item>
                <el-form-item label="预警类型">
                    <el-select v-model="searchForm.alert_type" placeholder="请选择预警类型" clearable>
                        <el-option v-for="option in alertTypeOptions" :key="option.value" :label="option.label"
                            :value="option.value" />
                    </el-select>
                </el-form-item>
                <el-form-item label="状态">
                    <el-select v-model="searchForm.is_resolved" placeholder="请选择" clearable>
                        <el-option label="已解决" value="true" />
                        <el-option label="未解决" value="false" />
                    </el-select>
                </el-form-item>
                <el-form-item label="创建日期">
                    <el-date-picker v-model="searchForm.start_date" type="date" placeholder="开始日期" style="width: 150px"
                        format="YYYY-MM-DD" value-format="YYYY-MM-DD" />
                    <span style="margin: 0 5px;">至</span>
                    <el-date-picker v-model="searchForm.end_date" type="date" placeholder="结束日期" style="width: 150px"
                        format="YYYY-MM-DD" value-format="YYYY-MM-DD" />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleSearch">查询</el-button>
                    <el-button @click="handleReset">重置</el-button>
                </el-form-item>
            </el-form>
        </div>

        <!-- 预警列表 -->
        <div class="alert-list">
            <el-table v-loading="loading" :data="alerts" stripe style="width: 100%">
                <el-table-column prop="alert_id" label="预警ID" width="180" show-overflow-tooltip />
                <el-table-column label="医院名称" width="180">
                    <template #default="scope">
                        <el-button link type="primary" @click="viewHospital(scope.row.hospital.hospital_id)">
                            {{ scope.row.hospital.name }}
                        </el-button>
                    </template>
                </el-table-column>
                <el-table-column label="预警类型" width="120">
                    <template #default="scope">
                        <el-tag :type="getAlertTypeClass(scope.row.alert_type)">
                            {{ scope.row.alert_type_display }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="message" label="预警内容" min-width="200" show-overflow-tooltip />
                <el-table-column label="状态" width="100">
                    <template #default="scope">
                        <el-tag :type="scope.row.is_resolved ? 'success' : 'danger'">
                            {{ scope.row.is_resolved ? '已解决' : '未解决' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="创建时间" width="150">
                    <template #default="scope">
                        {{ formatDate(scope.row.created_at) }}
                    </template>
                </el-table-column>
                <el-table-column label="解决时间" width="150">
                    <template #default="scope">
                        {{ scope.row.is_resolved ? formatDate(scope.row.resolved_time) : '-' }}
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="180" fixed="right">
                    <template #default="scope">
                        <el-button link type="primary" size="small" @click="handleDetail(scope.row)">查看详情</el-button>
                        <el-button link type="success" size="small" v-if="!scope.row.is_resolved"
                            @click="handleResolveAlert(scope.row)">解决</el-button>
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
.alert-container {
    padding: 20px;

    .search-form {
        background: rgba(0, 20, 45, 0.7);
        border: 1px solid rgba(0, 180, 220, 0.3);
        border-radius: 4px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .alert-list {
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
