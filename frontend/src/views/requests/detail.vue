<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getRequestDetail, updateRequestItemAllocation } from '@/api/modules/index';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { SupplyRequest, RequestItem } from '@/types/models';
import { Back, Link as IconLink, User, Calendar, Clock, StarFilled, Check, Memo, UploadFilled } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const requestId = route.params.id as string;

const requestDetail = ref<SupplyRequest | null>(null);
const loading = ref(false);
const saving = ref(false);

const editableItems = ref<RequestItem[]>([]);

const fetchRequestDetail = async () => {
    loading.value = true;
    try {
        const res = await getRequestDetail(requestId);
        if (res) {
            requestDetail.value = res;
            editableItems.value = JSON.parse(JSON.stringify(res.items || []));
        } else {
            ElMessage.error('未找到请求详情');
            router.push('/management/requests');
        }
    } catch (err) {
        console.error('获取请求详情失败', err);
        ElMessage.error('获取请求详情失败');
        router.push('/management/requests');
    } finally {
        loading.value = false;
    }
};

const goBack = () => {
    if (window.history.length > 1) {
        router.go(-1);
    } else {
        router.push('/management/requests');
    }
};

const viewHospital = () => {
    if (requestDetail.value?.hospital) {
        router.push(`/management/hospitals/${requestDetail.value.hospital}`);
    } else {
        ElMessage.warning('无法获取医院信息');
    }
};

const viewSupply = (supplyCode: string) => {
    router.push(`/management/supplies/${supplyCode}`);
};

const getStatusType = (status: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' => {
    switch (status) {
        case 'DF': return 'info';
        case 'SB': return 'primary';
        case 'AP': return 'warning';
        case 'FL': return 'success';
        case 'RJ': return 'danger';
        case 'CN': return 'warning';
        default: return 'info';
    }
};

const formatDateTime = (dateStr: string | null | undefined) => {
    if (!dateStr) return '-';
    try { return new Date(dateStr).toLocaleString(); } catch (e) { return dateStr; }
};

const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return '-';
    try { return new Date(dateStr).toLocaleDateString(); } catch (e) { return dateStr; }
};

const allocationRate = computed(() => {
    if (!editableItems.value || editableItems.value.length === 0) {
        return 0;
    }
    const totalRequested = editableItems.value.reduce((total, item) => total + (item.quantity || 0), 0);
    if (totalRequested === 0) return 100;

    const totalAllocated = editableItems.value.reduce((total, item) => total + (item.allocated || 0), 0);
    return Math.round((totalAllocated / totalRequested) * 100);
});

const allocationProgressColor = computed(() => {
    const rate = allocationRate.value;
    if (rate === 100) return '#67C23A';
    if (rate > 0) return '#E6A23C';
    return '#909399';
});

const getPersonName = (person: { first_name?: string, last_name?: string } | null | undefined): string => {
    if (!person) return '-';
    return `${person.first_name || ''} ${person.last_name || ''}`.trim() || '-';
};

const saveAllocation = async () => {
    if (!requestDetail.value || !editableItems.value) return;

    saving.value = true;
    const updatePromises: Promise<any>[] = [];
    const originalItems = requestDetail.value.items || [];

    editableItems.value.forEach((editedItem) => {
        const originalItem = originalItems.find(item => item.item_id === editedItem.item_id);

        if (originalItem && editedItem.allocated !== originalItem.allocated && editedItem.allocated != null) {
            if (editedItem.allocated < 0) {
                ElMessage.warning(`物资 "${editedItem.supply?.name}" 的分配数量不能为负数`);
                editedItem.allocated = originalItem.allocated;
                return;
            }
            if (editedItem.allocated > editedItem.quantity) {
                ElMessage.warning(`物资 "${editedItem.supply?.name}" 的分配数量 (${editedItem.allocated}) 不能超过请求数量 ${editedItem.quantity}`);
                editedItem.allocated = originalItem.allocated;
                return;
            }
            updatePromises.push(updateRequestItemAllocation(requestDetail.value!.request_id, editedItem.item_id, editedItem.allocated));
        }
    });

    if (updatePromises.length === 0) {
        ElMessage.info('分配数量没有变化');
        saving.value = false;
        return;
    }

    try {
        await Promise.all(updatePromises);
        ElMessage.success('分配数量已保存');
        await fetchRequestDetail();
    } catch (error: any) {
        console.error('保存分配数量失败', error);
        const errorMsg = error?.detail || error?.error || error?.message || '保存分配数量失败，请检查网络或联系管理员';
        ElMessage.error(errorMsg);
    } finally {
        saving.value = false;
    }
};

onMounted(() => {
    fetchRequestDetail();
});
</script>

<template>
    <div class="page-container request-detail-container">
        <div class="back-button-header">
            <el-button @click="goBack" :icon="Back">返回列表</el-button>
            <h2 class="page-title">物资请求详情</h2>
            <el-button v-if="requestDetail?.status === 'AP'" type="primary" :icon="UploadFilled" @click="saveAllocation"
                :loading="saving" style="margin-left: auto;">
                保存分配
            </el-button>
        </div>

        <div v-loading="loading" class="detail-content-wrapper">
            <template v-if="requestDetail">
                <div class="detail-card">
                    <div class="card-header">
                        <h3>基本信息: {{ requestDetail.request_id }}</h3>
                        <div class="status-tags">
                            <el-tag :type="getStatusType(requestDetail.status)" size="large" effect="dark">
                                {{ requestDetail.status_display || requestDetail.status }}
                            </el-tag>
                            <el-tag v-if="requestDetail.emergency" type="danger" size="large" effect="dark">
                                <el-icon>
                                    <StarFilled />
                                </el-icon> 紧急
                            </el-tag>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="label">医院名称:</span>
                                <span class="value">
                                    <el-button link type="primary" @click="viewHospital" :icon="IconLink">
                                        {{ requestDetail.hospital_name || requestDetail.hospital }}
                                    </el-button>
                                </span>
                            </div>
                            <div class="info-item">
                                <span class="label">请求人:</span>
                                <span class="value"><el-icon>
                                        <User />
                                    </el-icon> {{ getPersonName(requestDetail.requester) }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">优先得分:</span>
                                <span class="value"><el-rate v-model="requestDetail.priority" disabled size="small"
                                        style="vertical-align: middle;" /> ({{ requestDetail.priority?.toFixed(2)
                                        }})</span>
                            </div>
                            <div class="info-item">
                                <span class="label">请求时间:</span>
                                <span class="value"><el-icon>
                                        <Calendar />
                                    </el-icon> {{ formatDateTime(requestDetail.request_time) }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">需求时间:</span>
                                <span class="value"><el-icon>
                                        <Calendar />
                                    </el-icon> {{ formatDateTime(requestDetail.required_by) }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">紧急请求:</span>
                                <span class="value">
                                    <el-tag :type="requestDetail.emergency ? 'danger' : 'info'" size="small"
                                        effect="light">
                                        {{ requestDetail.emergency ? '是' : '否' }}
                                    </el-tag>
                                </span>
                            </div>
                            <div class="info-item">
                                <span class="label">审批人:</span>
                                <span class="value"><el-icon>
                                        <User />
                                    </el-icon> {{ getPersonName(requestDetail.approver) }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">审批时间:</span>
                                <span class="value"><el-icon>
                                        <Clock />
                                    </el-icon> {{ formatDateTime(requestDetail.approval_time) }}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">当前状态:</span>
                                <span class="value">
                                    <el-tag :type="getStatusType(requestDetail.status)" size="small" effect="light">
                                        {{ requestDetail.status_display || requestDetail.status }}
                                    </el-tag>
                                </span>
                            </div>
                        </div>
                        <div class="description-section">
                            <div class="label"><el-icon>
                                    <Memo />
                                </el-icon> 请求备注:</div>
                            <div class="value comments-display">
                                {{ requestDetail.comments || '暂无备注信息' }}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="detail-card">
                    <div class="card-header">
                        <h3>物资清单</h3>
                        <div class="allocation-info" v-if="editableItems && editableItems.length > 0">
                            <span>分配进度: </span>
                            <el-progress :percentage="allocationRate" :color="allocationProgressColor"
                                :stroke-width="10" status="success" style="width: 200px;" />
                        </div>
                    </div>
                    <div class="card-body">
                        <el-table :data="editableItems" style="width: 100%" border stripe empty-text="暂无物资项">
                            <el-table-column label="物资名称" min-width="200">
                                <template #default="scope">
                                    <el-button link type="primary" @click="viewSupply(scope.row.supply.unspsc_code)">
                                        {{ scope.row.supply?.name || '未知物资' }}
                                    </el-button>
                                    <div class="supply-code">编码: {{ scope.row.supply?.unspsc_code }}</div>
                                </template>
                            </el-table-column>
                            <el-table-column label="类别" width="120">
                                <template #default="scope">
                                    {{ scope.row.supply?.category_display || scope.row.supply?.category || '-' }}
                                </template>
                            </el-table-column>
                            <el-table-column label="请求数量" width="120" align="right">
                                <template #default="scope">
                                    {{ scope.row.quantity }} {{ scope.row.supply?.unit || '' }}
                                </template>
                            </el-table-column>
                            <el-table-column label="分配数量" width="150" align="right">
                                <template #default="scope">
                                    <el-input-number
                                        v-if="requestDetail.status === 'AP' || requestDetail.status === 'SB'"
                                        v-model="scope.row.allocated" :min="0" :max="scope.row.quantity" :step="1"
                                        size="small" controls-position="right" style="width: 120px;" />
                                    <span v-else>
                                        {{ scope.row.allocated ?? 0 }} {{ scope.row.supply?.unit || '' }}
                                    </span>
                                </template>
                            </el-table-column>
                            <el-table-column label="分配状态" width="110" align="center">
                                <template #default="scope">
                                    <el-tag :type="scope.row.allocated >= scope.row.quantity ? 'success' :
                                        scope.row.allocated > 0 ? 'warning' : 'info'" size="small" effect="light">
                                        {{ scope.row.allocated >= scope.row.quantity ? '已完成' :
                                            scope.row.allocated > 0 ? '部分分配' : '未分配' }}
                                    </el-tag>
                                </template>
                            </el-table-column>
                            <el-table-column prop="notes" label="物资备注" min-width="150" show-overflow-tooltip />
                        </el-table>
                    </div>
                </div>
            </template>
            <el-empty v-else-if="!loading" description="无法加载请求详情" />
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
            }
        }

        .status-tags {
            display: flex;
            gap: 10px;

            .el-tag {
                border: none;
            }

            .el-icon {
                vertical-align: middle;
                margin-right: 4px;
            }
        }

        .allocation-info {
            display: flex;
            align-items: center;
            gap: 10px;
            color: #ccc;
            font-size: 14px;
        }
    }

    .card-body {
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
                width: 90px;
                color: rgba(255, 255, 255, 0.7);
                flex-shrink: 0;
                margin-right: 10px;
                text-align: right;
                font-size: 14px;
            }

            .value {
                flex: 1;
                color: #fff;
                word-break: break-word;
                font-size: 14px;
                display: flex;
                align-items: center;

                .el-button--primary.is-link {
                    color: #00fdfa;
                    padding: 0;
                    height: auto;
                    line-height: inherit;

                    &:hover {
                        color: lighten(#00fdfa, 10%);
                    }

                    .el-icon {
                        margin-right: 3px;
                    }
                }

                .el-icon {
                    margin-right: 5px;
                    color: #ccc;
                    font-size: 16px;
                }

                .el-rate {
                    height: auto;

                    :deep(.el-rate__icon) {
                        font-size: 16px;
                    }
                }

                .el-tag--small {
                    height: 22px;
                    padding: 0 6px;
                    line-height: 20px;
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

        .el-table {
            :deep(.el-table__cell) {
                padding: 10px 12px;
                background-color: transparent;
                color: #ddd;
                border-color: rgba(0, 180, 220, 0.2);
            }

            :deep(th.el-table__cell) {
                background-color: rgba(0, 50, 80, 0.3);
                color: #00fdfa;
                font-weight: bold;
                border-color: rgba(0, 180, 220, 0.3);
            }

            :deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
                background-color: rgba(0, 30, 60, 0.15);
            }

            :deep(.el-table--border .el-table__inner-wrapper::after),
            :deep(.el-table--border::after),
            :deep(.el-table--border::before),
            :deep(.el-table__inner-wrapper::before) {
                background-color: rgba(0, 180, 220, 0.3);
            }

            .el-button--primary.is-link {
                color: #00fdfa;

                &:hover {
                    color: lighten(#00fdfa, 10%);
                }
            }

            .supply-code {
                font-size: 12px;
                color: #ccc;
                margin-top: 4px;
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
