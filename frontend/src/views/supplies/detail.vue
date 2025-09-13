<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getSupplyDetail, getInventoryBatches } from '@/api/modules/index';
import { ElMessage } from 'element-plus';
import type { MedicalSupply, InventoryBatch } from '@/types/models';
import { Back } from '@element-plus/icons-vue';
import * as json5 from 'json5';

const route = useRoute();
const router = useRouter();
const unspscCode = route.params.code as string;

const supply = ref<MedicalSupply | null>(null);
const inventoryBatches = ref<InventoryBatch[]>([]);
const inventoryTotal = ref(0);
const loading = reactive({
    supply: true,
    inventory: true
});
const inventoryPagination = reactive({
    currentPage: 1,
    pageSize: 10
});

// 获取物资详情
const fetchSupplyDetail = async () => {
    loading.supply = true;
    try {
        const res = await getSupplyDetail(unspscCode);
        if (res) {
            supply.value = res;
        } else {
            ElMessage.warning('未找到物资详情');
        }
    } catch (err) {
        console.error('获取物资详情失败', err);
        ElMessage.error('获取物资详情失败');
    } finally {
        loading.supply = false;
    }
};

// 获取库存批次
const fetchInventoryBatches = async () => {
    loading.inventory = true;
    try {
        const params = {
            supply: unspscCode,
            page: inventoryPagination.currentPage,
            page_size: inventoryPagination.pageSize
        };

        const res = await getInventoryBatches(params);
        if (res) {
            inventoryBatches.value = res.results || [];
            inventoryTotal.value = res.count || 0;
        } else {
            inventoryBatches.value = [];
            inventoryTotal.value = 0;
        }
    } catch (err) {
        console.error('获取库存批次失败', err);
        ElMessage.error('获取库存批次失败');
        inventoryBatches.value = [];
        inventoryTotal.value = 0;
    } finally {
        loading.inventory = false;
    }
};

// 库存批次分页变化
const handleInventoryPageChange = (page: number) => {
    inventoryPagination.currentPage = page;
    fetchInventoryBatches();
};

// 返回列表页
const goBack = () => {
    router.push('/management/supplies');
};

// 查看库存批次详情
const viewBatchDetail = (batch: InventoryBatch) => {
    router.push(`/management/inventory/${batch.batch_id}`);
};

// 查看医院详情
const viewHospitalDetail = (hospitalId: string | undefined) => {
    if (hospitalId) {
        router.push(`/management/hospitals/${hospitalId}`);
    }
};

// 格式化日期
const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
};

// 供应商联系信息解析 - 增加健壮性
const parsedSupplierContactInfo = computed(() => {
    const contactInfo = supply.value?.supplier?.contact_info;
    if (contactInfo && typeof contactInfo === 'string') {
        try {
            return JSON.parse(contactInfo);
        } catch (e) {
            console.warn("Failed to parse supplier contact_info with JSON.parse, trying json5:", contactInfo, e);
            try {
                return json5.parse(contactInfo);
            } catch (e2) {
                console.error("Failed to parse supplier contact_info with json5:", contactInfo, e2);
                return {};
            }
        }
    }
    return (typeof contactInfo === 'object' && contactInfo !== null) ? contactInfo : {};
});

onMounted(() => {
    fetchSupplyDetail();
    fetchInventoryBatches();
});
</script>

<template>
    <div class="supply-detail">
        <!-- 返回按钮 -->
        <div class="back-button">
            <el-button @click="goBack">
                <el-icon>
                    <Back />
                </el-icon> 返回列表
            </el-button>
        </div>

        <!-- 物资详情 -->
        <div class="detail-content">
            <!-- 物资基本信息卡片 -->
            <div class="detail-card" v-loading="loading.supply">
                <template v-if="supply">
                    <div class="card-header">
                        <h3>物资信息: {{ supply.name }}</h3>
                        <el-tag :type="supply.is_controlled ? 'warning' : 'info'" size="large" effect="dark">
                            {{ supply.is_controlled ? '受控物资' : '普通物资' }}
                        </el-tag>
                    </div>
                    <div class="card-body">
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="label">UNSPSC编码:</span>
                                <span class="value">{{ supply.unspsc_code }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">物资类型:</span>
                                <span class="value">{{ supply.category_display || '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">计量单位:</span>
                                <span class="value">{{ supply.unit || '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">执行标准:</span>
                                <span class="value">{{ supply.standard || '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">保质期:</span>
                                <span class="value">{{ supply.shelf_life ? `${supply.shelf_life}个月` : '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">存储温度:</span>
                                <span class="value">{{ supply.storage_temp || '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">最低库存:</span>
                                <span class="value">{{ supply.min_stock_level ?? '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">平均价格:</span>
                                <span class="value">{{ supply.avg_price !== null ? `¥ ${supply.avg_price}` : '-'
                                    }}</span>
                            </div>
                        </div>
                        <div class="description-section">
                            <div class="label">物资描述:</div>
                            <div class="value">{{ supply.description || '暂无描述' }}</div>
                        </div>
                    </div>
                </template>
                <el-empty v-else-if="!loading.supply" description="未找到物资数据" />
            </div>

            <!-- 供应商信息卡片 -->
            <div class="detail-card" v-if="!loading.supply && supply && supply.supplier">
                <div class="card-header">
                    <h3>供应商信息</h3>
                </div>
                <div class="card-body">
                    <div class="related-item">
                        <div class="related-title">{{ supply.supplier.name }}</div>
                        <div class="info-grid supplier-grid">
                            <div class="info-item">
                                <span class="label">联系人:</span>
                                <span class="value">{{ supply.supplier.contact_person || '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">联系电话:</span>
                                <span class="value">{{ parsedSupplierContactInfo.phone || '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">电子邮箱:</span>
                                <span class="value">{{ parsedSupplierContactInfo.email || '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">地址:</span>
                                <span class="value">{{ supply.supplier.address || parsedSupplierContactInfo.address ||
                                    '-' }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="detail-card" v-else-if="!loading.supply && supply">
                <div class="card-header">
                    <h3>供应商信息</h3>
                </div>
                <div class="card-body no-data">暂无供应商信息</div>
            </div>

            <!-- 库存批次列表卡片 -->
            <div class="detail-card" v-loading="loading.inventory">
                <div class="card-header">
                    <h3>相关库存批次</h3>
                </div>
                <div class="card-body">
                    <el-table :data="inventoryBatches" stripe style="width: 100%" v-if="inventoryBatches.length > 0">
                        <el-table-column prop="batch_number" label="批次号" width="180" show-overflow-tooltip />
                        <el-table-column label="所属医院" show-overflow-tooltip>
                            <template #default="scope">
                                <el-button link type="primary"
                                    @click="viewHospitalDetail(scope.row.hospital?.hospital_id)">
                                    {{ scope.row.hospital?.name || '未知医院' }}
                                </el-button>
                            </template>
                        </el-table-column>
                        <el-table-column prop="quantity" label="当前数量" width="100" align="right" />
                        <el-table-column label="生产日期" width="120" align="center">
                            <template #default="scope">{{ formatDate(scope.row.production_date) }}</template>
                        </el-table-column>
                        <el-table-column label="过期日期" width="120" align="center">
                            <template #default="scope">{{ formatDate(scope.row.expiration_date) }}</template>
                        </el-table-column>
                        <el-table-column label="入库日期" width="120" align="center">
                            <template #default="scope">{{ formatDate(scope.row.received_date) }}</template>
                        </el-table-column>
                        <el-table-column label="质检状态" width="100" align="center">
                            <template #default="scope">
                                <el-tag :type="scope.row.quality_check_passed ? 'success' : 'danger'" size="small">
                                    {{ scope.row.quality_check_passed ? '通过' : '未通过' }}
                                </el-tag>
                            </template>
                        </el-table-column>
                        <el-table-column label="操作" width="100" fixed="right" align="center">
                            <template #default="scope">
                                <el-button link type="primary" size="small" @click="viewBatchDetail(scope.row)">
                                    查看批次
                                </el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                    <el-empty v-else description="暂无相关库存批次" />

                    <!-- 库存批次分页 -->
                    <div class="pagination-container" v-if="inventoryTotal > 0">
                        <el-pagination v-model:currentPage="inventoryPagination.currentPage"
                            :page-size="inventoryPagination.pageSize" :total="inventoryTotal"
                            layout="total, prev, pager, next, jumper" @current-change="handleInventoryPageChange"
                            background small />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped lang="scss">
.detail-card {
    background: rgba(0, 20, 45, 0.7);
    border: 1px solid rgba(0, 180, 220, 0.3);
    border-radius: 4px;
    padding: 20px;
    margin-bottom: 20px;
    color: #fff;

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(0, 180, 220, 0.2);

        h3 {
            margin: 0;
            color: #00fdfa;
            font-size: 16px;
        }

        .el-button {
            font-size: 13px;
        }
    }

    .card-body {
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px 25px;

            &.supplier-grid {
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            }
        }

        .info-item,
        .related-info {
            display: flex;
            line-height: 1.6;

            .label {
                width: 90px;
                color: rgba(255, 255, 255, 0.7);
                flex-shrink: 0;
                margin-right: 10px;
                text-align: right;
            }

            .value {
                flex: 1;
                color: #fff;
                word-break: break-word;
            }
        }

        .description-section {
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid rgba(0, 180, 220, 0.1);

            .label {
                color: rgba(255, 255, 255, 0.7);
                margin-bottom: 8px;
                font-weight: 500;
            }

            .value {
                color: #fff;
                line-height: 1.7;
                font-size: 14px;
            }
        }

        .related-item {
            .related-title {
                font-size: 16px;
                font-weight: 500;
                color: #00fdfa;
                margin-bottom: 12px;
            }

            .related-info {
                margin-bottom: 8px;

                .label {
                    width: 60px;
                }
            }
        }

        .no-data {
            color: rgba(255, 255, 255, 0.5);
            font-style: italic;
            padding: 10px 0;
        }

        .pagination-container {
            margin-top: 20px;
            display: flex;
            justify-content: flex-end;
        }
    }
}

.supply-detail {
    padding: 20px;
    height: calc(100vh - 60px);
    overflow-y: auto;

    .back-button {
        margin-bottom: 20px;

        .el-button {
            background-color: rgba(0, 180, 220, 0.1);
            border-color: rgba(0, 180, 220, 0.3);
            color: #00fdfa;

            &:hover {
                background-color: rgba(0, 180, 220, 0.2);
                border-color: rgba(0, 180, 220, 0.5);
            }
        }
    }
}

::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb {
    background: rgba(0, 180, 220, 0.3);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 180, 220, 0.5);
}

@media (max-width: 768px) {
    .detail-card .card-body .info-grid {
        grid-template-columns: 1fr;
    }

    .detail-card .card-body .info-item .label {
        width: 80px;
        text-align: left;
    }
}
</style>
