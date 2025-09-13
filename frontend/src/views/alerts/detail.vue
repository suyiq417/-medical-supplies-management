<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getAlertDetail, resolveAlertById } from '@/api/modules/index';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { InventoryAlert } from '@/types/models';
import { Back, Link as IconLink, User, Calendar, Clock, WarningFilled, InfoFilled, SuccessFilled, CircleCheck, HomeFilled, Box, Goods } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const alertId = route.params.id as string;

const alertDetail = ref<InventoryAlert | null>(null);
const loading = ref(true);

// 获取预警详情
const fetchAlertDetail = async () => {
    loading.value = true;
    try {
        const res = await getAlertDetail(alertId);
        if (res) {
            alertDetail.value = res;
        } else {
            ElMessage.error('未找到预警详情');
            router.push('/management/alerts');
        }
    } catch (err) {
        console.error('获取预警详情失败', err);
        ElMessage.error('获取预警详情失败');
        router.push('/management/alerts');
    } finally {
        loading.value = false;
    }
};

// 返回列表
const goBack = () => {
    if (window.history.length > 1) {
        router.go(-1);
    } else {
        router.push('/management/alerts');
    }
};

// 查看医院
const viewHospital = () => {
    if (alertDetail.value?.hospital?.hospital_id) {
        router.push(`/management/hospitals/${alertDetail.value.hospital.hospital_id}`);
    } else {
        ElMessage.warning('无法获取医院信息');
    }
};

// 查看物资
const viewSupply = () => {
    if (alertDetail.value?.supply?.unspsc_code) {
        router.push(`/management/supplies/${alertDetail.value.supply.unspsc_code}`);
    } else {
        ElMessage.warning('无法获取物资信息');
    }
};

// 查看库存批次
const viewBatch = () => {
    if (alertDetail.value?.inventory_batch?.batch_id) {
        router.push(`/management/inventory/${alertDetail.value.inventory_batch.batch_id}`);
    } else {
        ElMessage.warning('无法获取批次信息');
    }
};

// 解决预警
const handleResolveAlert = async () => {
    try {
        await ElMessageBox.confirm('确认将此预警标记为已解决吗？', '确认解决', {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            type: 'warning'
        });

        loading.value = true;
        const res = await resolveAlertById(alertId);
        if (res) {
            ElMessage.success('预警已标记为已解决');
            await fetchAlertDetail();
        } else {
            ElMessage.error('解决预警操作失败');
        }
    } catch (err) {
        if (err !== 'cancel') {
            console.error('解决预警失败', err);
            ElMessage.error('解决预警失败');
        }
    } finally {
        if (loading.value) loading.value = false;
    }
};

// 获取预警类型样式
const getAlertTypeClass = (type: string | undefined): 'success' | 'warning' | 'info' | 'danger' => {
    switch (type) {
        case 'LS': return 'warning';
        case 'EX': return 'info';
        case 'ED': return 'danger';
        case 'CP': return 'success';
        default: return 'info';
    }
};

// 获取解决状态样式
const getResolvedStatusClass = (isResolved: boolean | undefined): 'success' | 'danger' => {
    return isResolved ? 'success' : 'danger';
};

// 格式化日期时间
const formatDateTime = (dateStr: string | null | undefined) => {
    if (!dateStr) return '-';
    try {
        return new Date(dateStr).toLocaleString();
    } catch (e) {
        return dateStr;
    }
};

// 格式化日期
const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return '-';
    try {
        return new Date(dateStr).toLocaleDateString();
    } catch (e) {
        return dateStr;
    }
};

// 获取人员姓名
const getPersonName = (person: { first_name?: string, last_name?: string } | null | undefined): string => {
    if (!person) return '-';
    return `${person.first_name || ''} ${person.last_name || ''}`.trim() || '-';
};

onMounted(() => {
    fetchAlertDetail();
});
</script>

<template>
    <div class="page-container alert-detail-container">
        <div class="back-button-header">
            <el-button @click="goBack" :icon="Back">返回列表</el-button>
            <h2 class="page-title">预警详情</h2>
        </div>

        <div v-loading="loading" class="detail-content-wrapper">
            <template v-if="alertDetail">
                <div class="detail-card">
                    <div class="card-header">
                        <h3>预警 #{{ alertDetail.alert_id }}</h3>
                        <div class="status-tags">
                            <el-tag :type="getAlertTypeClass(alertDetail.alert_type)" size="large" effect="dark">
                                <el-icon>
                                    <component
                                        :is="alertDetail.alert_type === 'LS' ? WarningFilled : alertDetail.alert_type === 'ED' ? WarningFilled : InfoFilled" />
                                </el-icon>
                                {{ alertDetail.alert_type_display || alertDetail.alert_type }}
                            </el-tag>
                            <el-tag :type="getResolvedStatusClass(alertDetail.is_resolved)" size="large" effect="dark">
                                <el-icon>
                                    <component :is="alertDetail.is_resolved ? CircleCheck : WarningFilled" />
                                </el-icon>
                                {{ alertDetail.is_resolved ? '已解决' : '未解决' }}
                            </el-tag>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="alert-message-display">
                            {{ alertDetail.message || '无详细预警信息' }}
                        </div>
                        <div class="info-grid timestamps-grid">
                            <div class="info-item">
                                <span class="label"><el-icon>
                                        <Calendar />
                                    </el-icon>创建时间:</span>
                                <span class="value">{{ formatDateTime(alertDetail.created_at) }}</span>
                            </div>
                            <div class="info-item" v-if="alertDetail.is_resolved">
                                <span class="label"><el-icon>
                                        <Clock />
                                    </el-icon>解决时间:</span>
                                <span class="value">{{ formatDateTime(alertDetail.resolved_time) }}</span>
                            </div>
                        </div>
                        <div v-if="!alertDetail.is_resolved" class="action-buttons">
                            <el-button type="primary" @click="handleResolveAlert" :icon="CircleCheck">标记为已解决</el-button>
                        </div>
                    </div>
                </div>

                <div class="detail-card">
                    <div class="card-header">
                        <h3><el-icon>
                                <HomeFilled />
                            </el-icon>医院信息</h3>
                        <el-button link type="primary" @click="viewHospital" :icon="IconLink">查看医院详情</el-button>
                    </div>
                    <div class="card-body">
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="label">医院名称:</span>
                                <span class="value">{{ alertDetail.hospital?.name || '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">医院等级:</span>
                                <span class="value">{{ alertDetail.hospital?.level_display || '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">所在地区:</span>
                                <span class="value">{{ alertDetail.hospital?.region || '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">详细地址:</span>
                                <span class="value">{{ alertDetail.hospital?.address || '-' }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="detail-card" v-if="alertDetail?.supply">
                    <div class="card-header">
                        <h3><el-icon>
                                <Goods />
                            </el-icon>相关物资</h3>
                        <el-button link type="primary" @click="viewSupply" :icon="IconLink">查看物资详情</el-button>
                    </div>
                    <div class="card-body">
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="label">物资名称:</span>
                                <span class="value">{{ alertDetail.supply.name }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">分类:</span>
                                <span class="value">{{ alertDetail.supply.category_display || '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">单位:</span>
                                <span class="value">{{ alertDetail.supply.unit || '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">当前库存:</span>
                                <span class="value">{{ alertDetail.current_quantity ?? '-' }} {{ alertDetail.supply.unit
                                    || '' }}</span>
                            </div>
                            <div class="info-item" v-if="alertDetail.alert_type === 'LS'">
                                <span class="label">最低库存要求:</span>
                                <span class="value">{{ alertDetail.supply.min_stock_level ?? '-' }} {{
                                    alertDetail.supply.unit || '' }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="detail-card" v-if="alertDetail?.inventory_batch">
                    <div class="card-header">
                        <h3><el-icon>
                                <Box />
                            </el-icon>相关批次</h3>
                        <el-button link type="primary" @click="viewBatch" :icon="IconLink">查看批次详情</el-button>
                    </div>
                    <div class="card-body">
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="label">批次号:</span>
                                <span class="value">{{ alertDetail.inventory_batch.batch_number || '-' }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">数量:</span>
                                <span class="value">{{ alertDetail.inventory_batch.quantity ?? '-' }} {{
                                    alertDetail.supply?.unit || '' }}</span>
                            </div>
                            <div class="info-item"
                                v-if="alertDetail.alert_type === 'EX' || alertDetail.alert_type === 'ED'">
                                <span class="label">过期日期:</span>
                                <span class="value"><el-icon>
                                        <Calendar />
                                    </el-icon>{{ formatDate(alertDetail.inventory_batch.expiration_date) }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">生产日期:</span>
                                <span class="value"><el-icon>
                                        <Calendar />
                                    </el-icon>{{ formatDate(alertDetail.inventory_batch.production_date) }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="detail-card" v-if="alertDetail?.is_resolved">
                    <div class="card-header">
                        <h3><el-icon>
                                <SuccessFilled />
                            </el-icon>解决信息</h3>
                    </div>
                    <div class="card-body">
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="label"><el-icon>
                                        <Clock />
                                    </el-icon>解决时间:</span>
                                <span class="value">{{ formatDateTime(alertDetail.resolved_time) }}</span>
                            </div>
                            <div class="info-item" v-if="alertDetail.resolved_by">
                                <span class="label"><el-icon>
                                        <User />
                                    </el-icon>解决人员:</span>
                                <span class="value">{{ getPersonName(alertDetail.resolved_by) }}</span>
                            </div>
                        </div>
                        <div class="description-section" v-if="alertDetail.resolution_notes">
                            <div class="label">解决备注:</div>
                            <div class="value comments-display">
                                {{ alertDetail.resolution_notes }}
                            </div>
                        </div>
                    </div>
                </div>
            </template>
            <el-empty v-else-if="!loading" description="无法加载预警详情" />
        </div>
    </div>
</template>

<style scoped lang="scss">
.page-container {
    padding: 20px;
    height: calc(100vh - 60px);
    overflow-y: auto;
    background-color: #03050C;
    color: #fff;
}

.back-button-header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    gap: 15px;

    .el-button {
        background-color: rgba(0, 180, 220, 0.1);
        border-color: rgba(0, 180, 220, 0.3);
        color: #00fdfa;
        padding: 8px 15px;

        &:hover {
            background-color: rgba(0, 180, 220, 0.2);
            border-color: rgba(0, 180, 220, 0.5);
        }

        .el-icon {
            margin-right: 5px;
        }
    }

    .page-title {
        color: #00fdfa;
        margin: 0;
        font-size: 20px;
        flex-grow: 1;
    }
}

.detail-content-wrapper {}

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
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid rgba(0, 180, 220, 0.2);

        h3 {
            margin: 0;
            color: #00fdfa;
            font-size: 18px;
            display: flex;
            align-items: center;

            .el-icon {
                margin-right: 8px;
                font-size: 20px;
            }
        }

        .status-tags {
            display: flex;
            gap: 10px;

            .el-tag {
                border: none;

                .el-icon {
                    vertical-align: middle;
                    margin-right: 4px;
                }
            }
        }

        .el-button--primary.is-link {
            color: #00fdfa;

            &:hover {
                color: lighten(#00fdfa, 10%);
            }

            .el-icon {
                margin-right: 3px;
            }
        }
    }

    .card-body {
        .alert-message-display {
            font-size: 15px;
            color: #eee;
            white-space: pre-line;
            line-height: 1.7;
            background-color: rgba(0, 30, 60, 0.2);
            padding: 15px;
            border-radius: 4px;
            border: 1px solid rgba(0, 180, 220, 0.1);
            margin-bottom: 20px;
        }

        .timestamps-grid {
            margin-bottom: 20px;
            gap: 10px 20px;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        }

        .action-buttons {
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid rgba(0, 180, 220, 0.1);
            display: flex;
            justify-content: flex-end;
        }

        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 15px 25px;
        }

        .info-item {
            display: flex;
            line-height: 1.8;
            align-items: center;

            .label {
                width: 100px;
                color: rgba(255, 255, 255, 0.7);
                flex-shrink: 0;
                margin-right: 10px;
                text-align: right;
                font-size: 14px;

                .el-icon {
                    margin-right: 5px;
                    vertical-align: middle;
                    font-size: 16px;
                }
            }

            .value {
                flex: 1;
                color: #fff;
                word-break: break-word;
                font-size: 14px;
                display: flex;
                align-items: center;

                .el-icon {
                    margin-right: 5px;
                    color: #ccc;
                    font-size: 16px;
                }
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
                font-size: 14px;
            }

            .value.comments-display {
                color: #eee;
                white-space: pre-line;
                line-height: 1.7;
                background-color: rgba(0, 30, 60, 0.2);
                padding: 15px;
                border-radius: 4px;
                border: 1px solid rgba(0, 180, 220, 0.1);
                min-height: 60px;
                font-size: 14px;
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
        width: 90px;
        text-align: left;
    }

    .back-button-header {
        flex-direction: column;
        align-items: flex-start;

        .page-title {
            margin-top: 10px;
        }
    }
}

:deep(.el-loading-mask) {
    background-color: rgba(3, 5, 12, 0.7);
}

:deep(.el-empty__description p) {
    color: #ccc;
}

:deep(.el-empty__image) {}
</style>
