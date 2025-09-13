<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getInventoryBatchDetail } from '@/api/modules/index';
import { ElMessage } from 'element-plus';
import type { InventoryBatch } from '@/types/models';
import { Back } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const batchId = route.params.id as string;

const batchDetail = ref<InventoryBatch | null>(null);
const loading = ref(true);

// 获取批次详情
const fetchBatchDetail = async () => {
    loading.value = true;
    try {
        const res = await getInventoryBatchDetail(batchId);
        if (res) {
            batchDetail.value = res;
        } else {
            ElMessage.warning('未找到批次详情');
        }
    } catch (err) {
        console.error('获取批次详情失败', err);
        ElMessage.error('获取批次详情失败');
    } finally {
        loading.value = false;
    }
};

// 返回列表页 - 修正路径
const goBack = () => {
    router.push('/management/inventory');
};

// 跳转到医院详情 - 修正路径
const viewHospital = () => {
    if (batchDetail.value?.hospital?.hospital_id) {
        router.push(`/management/hospitals/${batchDetail.value.hospital.hospital_id}`);
    }
};

// 跳转到物资详情 - 修正路径
const viewSupply = () => {
    if (batchDetail.value?.supply?.unspsc_code) {
        router.push(`/management/supplies/${batchDetail.value.supply.unspsc_code}`);
    }
};

// 格式化日期
const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
};

// 格式化日期时间
const formatDateTime = (dateStr: string | null | undefined) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
};

// 计算剩余保质期天数
const calculateDaysRemaining = (dateStr: string | null | undefined) => {
    if (!dateStr) return { days: null, isExpired: false, isWarning: false };

    try {
        const expirationDate = new Date(dateStr);
        if (isNaN(expirationDate.getTime())) {
            return { days: null, isExpired: false, isWarning: false };
        }
        const now = new Date();
        expirationDate.setHours(0, 0, 0, 0);
        now.setHours(0, 0, 0, 0);

        const diffTime = expirationDate.getTime() - now.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        return {
            days: diffDays,
            isExpired: diffDays < 0,
            isWarning: diffDays >= 0 && diffDays <= 30
        };
    } catch (e) {
        console.error("Error calculating days remaining:", e);
        return { days: null, isExpired: false, isWarning: false };
    }
};

// 计算总价值
const totalValue = computed(() => {
    if (batchDetail.value?.unit_price && batchDetail.value?.quantity) {
        try {
            const price = parseFloat(batchDetail.value.unit_price.toString());
            const quantity = parseInt(batchDetail.value.quantity.toString(), 10);
            if (!isNaN(price) && !isNaN(quantity)) {
                return (price * quantity).toFixed(2);
            }
        } catch {
            return '计算错误';
        }
    }
    return '暂无';
});

// 获取入库人员姓名，优先显示全名，否则显示用户名
const receivedByName = computed(() => {
    const user = batchDetail.value?.received_by;
    if (!user) return '未知';
    if (user.first_name || user.last_name) {
        return `${user.first_name || ''} ${user.last_name || ''}`.trim();
    }
    return user.username || '未知';
});

// 解析 contact_info 的计算属性
const parsedContactInfo = computed(() => {
    const contactInfo = batchDetail.value?.supplier?.contact_info;
    if (contactInfo && typeof contactInfo === 'string') {
        try {
            const parsed = JSON.parse(contactInfo);
            return typeof parsed === 'object' && parsed !== null ? parsed : {};
        } catch (e) {
            console.error("Failed to parse supplier contact_info string:", contactInfo, e);
            return {};
        }
    }
    return typeof contactInfo === 'object' && contactInfo !== null ? contactInfo : {};
});

// 解析 storage_condition 的计算属性
const parsedStorageCondition = computed(() => {
    const storageCondition = batchDetail.value?.storage_condition;
    if (storageCondition && typeof storageCondition === 'string') {
        try {
            const parsed = JSON.parse(storageCondition);
            return typeof parsed === 'object' && parsed !== null ? parsed : {};
        } catch (e) {
            console.error("Failed to parse storage_condition string:", storageCondition, e);
            return {};
        }
    }
    return typeof storageCondition === 'object' && storageCondition !== null ? storageCondition : {};
});

onMounted(() => {
    fetchBatchDetail();
});
</script>

<template>
    <div class="batch-detail">
        <!-- 返回按钮 -->
        <div class="back-button">
            <el-button @click="goBack">
                <el-icon>
                    <Back />
                </el-icon> 返回列表
            </el-button>
        </div>

        <!-- 批次详情 -->
        <div class="detail-content" v-loading="loading">
            <template v-if="batchDetail">
                <div class="detail-header">
                    <h2 class="batch-title">批次详情: {{ batchDetail.batch_number }}</h2>
                    <el-tag :type="batchDetail.quality_check_passed ? 'success' : 'danger'" size="large" effect="dark">
                        {{ batchDetail.quality_check_passed ? '质检通过' : '质检未通过' }}
                    </el-tag>
                </div>

                <el-divider />

                <!-- 基本信息卡片 -->
                <div class="detail-card">
                    <div class="card-header">
                        <h3>基本信息</h3>
                    </div>
                    <div class="card-body">
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="label">批次编号:</span>
                                <span class="value">{{ batchDetail.batch_number }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">数量:</span>
                                <span class="value">{{ batchDetail.quantity }} {{ batchDetail.supply?.unit || ''
                                    }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">生产日期:</span>
                                <span class="value">{{ formatDate(batchDetail.production_date) }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">过期日期:</span>
                                <span class="value" :class="{
                                    'text-danger': calculateDaysRemaining(batchDetail.expiration_date).isExpired,
                                    'text-warning': !calculateDaysRemaining(batchDetail.expiration_date).isExpired && calculateDaysRemaining(batchDetail.expiration_date).isWarning
                                }">
                                    {{ formatDate(batchDetail.expiration_date) }}
                                    <span v-if="calculateDaysRemaining(batchDetail.expiration_date).days !== null">
                                        <span v-if="calculateDaysRemaining(batchDetail.expiration_date).isExpired">
                                            (已过期 {{ Math.abs(calculateDaysRemaining(batchDetail.expiration_date).days!)
                                            }} 天)
                                        </span>
                                        <span v-else-if="calculateDaysRemaining(batchDetail.expiration_date).isWarning">
                                            (剩余 {{ calculateDaysRemaining(batchDetail.expiration_date).days }} 天)
                                        </span>
                                        <span v-else>
                                            (剩余 {{ calculateDaysRemaining(batchDetail.expiration_date).days }} 天)
                                        </span>
                                    </span>
                                </span>
                            </div>
                            <div class="info-item">
                                <span class="label">入库日期:</span>
                                <span class="value">{{ formatDate(batchDetail.received_date) }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">入库人员:</span>
                                <span class="value">{{ receivedByName }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">单价:</span>
                                <span class="value">¥ {{ batchDetail.unit_price || '暂无' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">总价值:</span>
                                <span class="value">¥ {{ totalValue }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">创建时间:</span>
                                <span class="value">{{ formatDateTime(batchDetail.created_at) }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">更新时间:</span>
                                <span class="value">{{ formatDateTime(batchDetail.updated_at) }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 关联信息卡片 -->
                <div class="detail-row">
                    <!-- 医院信息 -->
                    <div class="detail-card">
                        <div class="card-header">
                            <h3>所属医院</h3>
                            <el-button v-if="batchDetail.hospital" link type="primary"
                                @click="viewHospital">查看详情</el-button>
                        </div>
                        <div class="card-body">
                            <div v-if="batchDetail.hospital" class="related-item">
                                <div class="related-title">{{ batchDetail.hospital.name }}</div>
                                <div class="related-info">
                                    <span class="label">等级:</span>
                                    <span class="value">{{ batchDetail.hospital.level_display || '-' }}</span>
                                </div>
                                <div class="related-info">
                                    <span class="label">地区:</span>
                                    <span class="value">{{ batchDetail.hospital.region || '-' }}</span>
                                </div>
                                <div class="related-info">
                                    <span class="label">地址:</span>
                                    <span class="value">{{ batchDetail.hospital.address || '-' }}</span>
                                </div>
                            </div>
                            <div v-else class="no-data">暂无医院信息</div>
                        </div>
                    </div>

                    <!-- 物资信息 -->
                    <div class="detail-card">
                        <div class="card-header">
                            <h3>关联物资</h3>
                            <el-button v-if="batchDetail.supply" link type="primary"
                                @click="viewSupply">查看详情</el-button>
                        </div>
                        <div class="card-body">
                            <div v-if="batchDetail.supply" class="related-item">
                                <div class="related-title">{{ batchDetail.supply.name }}</div>
                                <div class="related-info">
                                    <span class="label">分类:</span>
                                    <span class="value">{{ batchDetail.supply.category_display || '-' }}</span>
                                </div>
                                <div class="related-info">
                                    <span class="label">单位:</span>
                                    <span class="value">{{ batchDetail.supply.unit || '-' }}</span>
                                </div>
                                <div class="related-info">
                                    <span class="label">保质期:</span>
                                    <span class="value">{{ batchDetail.supply.shelf_life ?
                                        `${batchDetail.supply.shelf_life}个月` : '-' }}</span>
                                </div>
                                <div class="related-info">
                                    <span class="label">受控:</span>
                                    <span class="value">
                                        <el-tag :type="batchDetail.supply.is_controlled ? 'warning' : 'info'"
                                            size="small" effect="dark">
                                            {{ batchDetail.supply.is_controlled ? '是' : '否' }}
                                        </el-tag>
                                    </span>
                                </div>
                            </div>
                            <div v-else class="no-data">暂无物资信息</div>
                        </div>
                    </div>
                </div>

                <!-- 供应商信息卡片 -->
                <div class="detail-card" v-if="batchDetail.supplier">
                    <div class="card-header">
                        <h3>供应商信息</h3>
                    </div>
                    <div class="card-body">
                        <div class="related-item">
                            <div class="related-title">{{ batchDetail.supplier.name }}</div>
                            <div class="info-grid supplier-grid">
                                <div class="info-item">
                                    <span class="label">联系人:</span>
                                    <span class="value">{{ batchDetail.supplier.contact_person }}</span>
                                </div>
                                <div class="info-item">
                                    <span class="label">联系电话:</span>
                                    <span class="value">{{ parsedContactInfo.phone || '-' }}</span>
                                </div>
                                <div class="info-item">
                                    <span class="label">电子邮箱:</span>
                                    <span class="value">{{ parsedContactInfo.email || '-' }}</span>
                                </div>
                                <div class="info-item">
                                    <span class="label">地址:</span>
                                    <span class="value">{{ batchDetail.supplier.address || '-' }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="detail-card" v-else>
                    <div class="card-header">
                        <h3>供应商信息</h3>
                    </div>
                    <div class="card-body no-data">暂无供应商信息</div>
                </div>

                <!-- 存储条件卡片 -->
                <div class="detail-card">
                    <div class="card-header">
                        <h3>存储条件</h3>
                    </div>
                    <div class="card-body">
                        <div v-if="Object.keys(parsedStorageCondition).length > 0" class="storage-conditions">
                            <div class="info-grid storage-grid">
                                <div class="info-item" v-if="parsedStorageCondition.temperature">
                                    <span class="label">温度要求:</span>
                                    <span class="value">{{ parsedStorageCondition.temperature }}</span>
                                </div>
                                <div class="info-item" v-if="parsedStorageCondition.humidity">
                                    <span class="label">湿度要求:</span>
                                    <span class="value">{{ parsedStorageCondition.humidity }}</span>
                                </div>
                                <div class="info-item" v-if="parsedStorageCondition.light">
                                    <span class="label">光照要求:</span>
                                    <span class="value">{{ parsedStorageCondition.light }}</span>
                                </div>
                                <div class="info-item notes-item" v-if="parsedStorageCondition.notes">
                                    <span class="label">特殊说明:</span>
                                    <span class="value">{{ parsedStorageCondition.notes }}</span>
                                </div>
                            </div>
                        </div>
                        <div v-else class="no-data">暂无特定存储条件信息</div>
                    </div>
                </div>

                <!-- 备注信息 -->
                <div class="detail-card">
                    <div class="card-header">
                        <h3>备注</h3>
                    </div>
                    <div class="card-body">
                        <div class="notes">
                            {{ batchDetail.notes || '暂无备注信息' }}
                        </div>
                    </div>
                </div>
            </template>
            <el-empty v-else-if="!loading" description="未找到批次数据" />
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
            grid-template-columns: repeat(2, 1fr);
            gap: 15px 25px;

            &.supplier-grid,
            &.storage-grid {
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            }

            &.storage-grid .notes-item {
                grid-column: 1 / -1;
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

        .storage-conditions,
        .notes {
            color: #fff;
            line-height: 1.7;
            font-size: 14px;
        }

        .no-data {
            color: rgba(255, 255, 255, 0.5);
            font-style: italic;
            padding: 10px 0;
        }
    }
}

.batch-detail {
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

    .detail-content {
        .detail-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;

            .batch-title {
                margin: 0;
                color: #00fdfa;
                font-size: 20px;
                font-weight: 600;
            }
        }

        .el-divider {
            background-color: rgba(0, 180, 220, 0.3);
            margin: 15px 0 25px 0;
        }

        .detail-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;

            .detail-card {
                margin-bottom: 0;
            }
        }

        .text-danger {
            color: #F56C6C;
            font-weight: bold;
        }

        .text-warning {
            color: #E6A23C;
            font-weight: bold;
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

@media (max-width: 992px) {
    .detail-content .detail-row {
        grid-template-columns: 1fr;
    }
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
