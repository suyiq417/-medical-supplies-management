<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getHospitals } from '@/api/modules/index';
import { ElMessage } from 'element-plus';
import type { Hospital } from '@/types/models';

const router = useRouter();
const hospitals = ref<Hospital[]>([]);
const loading = ref(true);
const total = ref(0);

// 搜索表单
const searchForm = reactive({
    name: '',
    region: '',
    level: ''
});

// 医院等级选项
const levelOptions = [
    { label: '社区医院', value: 1 },
    { label: '区级医院', value: 2 },
    { label: '三甲医院', value: 3 },
    { label: '三乙医院', value: 4 },
    { label: '二甲医院', value: 5 },
    { label: '二乙医院', value: 6 },
    { label: '一甲医院', value: 7 },
    { label: '一乙医院', value: 8 },
    { label: '其他', value: 9 }
];

// 分页配置
const pagination = reactive({
    currentPage: 1,
    pageSize: 10
});

// 获取医院列表
const fetchHospitals = async () => {
    loading.value = true;
    try {
        const params = {
            name: searchForm.name,
            region: searchForm.region,
            level: searchForm.level,
            page: pagination.currentPage,
            page_size: pagination.pageSize
        };

        const res = await getHospitals(params);
        if (res) {
            hospitals.value = res.results || res;
            total.value = res.count || hospitals.value.length;
        }
    } catch (err) {
        console.error('获取医院列表失败', err);
        ElMessage.error('获取医院列表失败');
    } finally {
        loading.value = false;
    }
};

// 搜索
const handleSearch = () => {
    pagination.currentPage = 1;
    fetchHospitals();
};

// 重置
const handleReset = () => {
    searchForm.name = '';
    searchForm.region = '';
    searchForm.level = '';
    pagination.currentPage = 1;
    fetchHospitals();
};

// 分页变化
const handlePageChange = (page: number) => {
    pagination.currentPage = page;
    fetchHospitals();
};

// 查看详情
const handleDetail = (hospital: Hospital) => {
    router.push(`/management/hospitals/${hospital.hospital_id}`);
};

onMounted(() => {
    fetchHospitals();
});
</script>

<template>
    <div class="hospital-container">
        <!-- 搜索表单 -->
        <div class="search-form">
            <el-form :model="searchForm" inline>
                <el-form-item label="医院名称">
                    <el-input v-model="searchForm.name" placeholder="请输入医院名称" clearable />
                </el-form-item>
                <el-form-item label="所属地区">
                    <el-input v-model="searchForm.region" placeholder="请输入所属地区" clearable />
                </el-form-item>
                <el-form-item label="医院等级">
                    <el-select v-model="searchForm.level" placeholder="请选择医院等级" clearable>
                        <el-option v-for="item in levelOptions" :key="item.value" :label="item.label"
                            :value="item.value" />
                    </el-select>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleSearch">查询</el-button>
                    <el-button @click="handleReset">重置</el-button>
                </el-form-item>
            </el-form>
        </div>

        <!-- 医院列表 -->
        <div class="hospital-list">
            <el-table v-loading="loading" :data="hospitals" stripe style="width: 100%">
                <el-table-column prop="name" label="医院名称" width="200" show-overflow-tooltip />
                <el-table-column prop="level_display" label="医院等级" width="100" />
                <el-table-column prop="region" label="所属地区" width="120" />
                <el-table-column prop="address" label="详细地址" show-overflow-tooltip />
                <el-table-column prop="is_active" label="状态" width="80">
                    <template #default="scope">
                        <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                            {{ scope.row.is_active ? '启用' : '禁用' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="150" fixed="right">
                    <template #default="scope">
                        <el-button link type="primary" size="small" @click="handleDetail(scope.row)">查看</el-button>
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
.hospital-container {
    padding: 20px;

    .search-form {
        background: rgba(0, 20, 45, 0.7);
        border: 1px solid rgba(0, 180, 220, 0.3);
        border-radius: 4px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .hospital-list {
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
