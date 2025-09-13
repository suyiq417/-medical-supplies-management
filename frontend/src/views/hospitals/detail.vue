<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getHospitalDetail, getInventoryBatches, getInventoryAlertsList } from '@/api/modules/index';
import { ElMessage } from 'element-plus';
import * as echarts from 'echarts';
import type { Hospital, InventoryBatch, InventoryAlert } from '@/types/models';
import { ArrowLeft, InfoFilled } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const hospitalId = route.params.id as string;

const hospital = ref<Hospital | null>(null);
const inventoryBatches = ref<InventoryBatch[]>([]);
const alerts = ref<InventoryAlert[]>([]);
const loading = ref({
    hospital: true,
    inventory: true,
    alerts: true
});

const pieChartRef = ref<HTMLElement | null>(null);
let pieChart: echarts.ECharts | null = null;

// 计算库存使用率
const capacityUsage = computed(() => {
    if (hospital.value && hospital.value.storage_volume > 0) {
        const usage = (hospital.value.current_capacity / hospital.value.storage_volume) * 100;
        return Math.min(100, Math.max(0, parseFloat(usage.toFixed(1))));
    }
    return 0;
});

// 计算库存使用率的颜色状态
const capacityStatusColor = computed(() => {
    if (!hospital.value || hospital.value.storage_volume <= 0) return '#67C23A';
    const usage = capacityUsage.value;
    const threshold = hospital.value.warning_threshold || 20;
    if (usage >= threshold) return '#F56C6C';
    if (usage >= threshold * 0.8) return '#E6A23C';
    return '#67C23A';
});

// 获取医院详情
const fetchHospitalDetail = async () => {
    loading.value.hospital = true;
    try {
        const res = await getHospitalDetail(hospitalId);
        if (res) {
            hospital.value = res;
        }
    } catch (err) {
        console.error('获取医院详情失败', err);
        ElMessage.error('获取医院详情失败');
    } finally {
        loading.value.hospital = false;
    }
};

// 获取库存批次
const fetchInventoryBatches = async () => {
    loading.value.inventory = true;
    try {
        const res = await getInventoryBatches({ hospital_id: hospitalId, page_size: 1000 });
        if (res) {
            inventoryBatches.value = res.results || res;
            initPieChart();
        }
    } catch (err) {
        console.error('获取库存批次失败', err);
        ElMessage.error('获取库存批次失败');
    } finally {
        loading.value.inventory = false;
    }
};

// 获取预警信息
const fetchAlerts = async () => {
    loading.value.alerts = true;
    try {
        const res = await getInventoryAlertsList({
            hospital_id: hospitalId,
            is_resolved: false,
            page_size: 5
        });
        if (res) {
            alerts.value = res.results || res;
        }
    } catch (err) {
        console.error('获取预警信息失败', err);
        ElMessage.error('获取预警信息失败');
    } finally {
        loading.value.alerts = false;
    }
};

// 初始化饼图
const initPieChart = () => {
    if (!pieChartRef.value) return;

    if (!inventoryBatches.value.length) {
        pieChart?.clear();
        pieChart?.dispose();
        pieChart = null;
    } else {
        const categoryMap = new Map<string, number>();
        inventoryBatches.value.forEach(batch => {
            const category = batch.supply?.category_display || '未知类别';
            const quantity = typeof batch.quantity === 'number' ? batch.quantity : 0;
            categoryMap.set(category, (categoryMap.get(category) || 0) + quantity);
        });

        const pieData = Array.from(categoryMap.entries())
            .filter(([name, value]) => value > 0)
            .map(([name, value]) => ({ name, value }));

        if (!pieData.length) {
            pieChart?.clear();
            pieChart?.dispose();
            pieChart = null;
            return;
        }

        if (pieChart) {
            pieChart.dispose();
        }

        pieChart = echarts.init(pieChartRef.value);

        const option = {
            tooltip: {
                trigger: 'item',
                formatter: '{a} <br/>{b}: {c} ({d}%)',
                backgroundColor: 'rgba(0, 20, 45, 0.8)',
                borderColor: 'rgba(0, 180, 220, 0.5)',
                textStyle: {
                    color: '#fff'
                }
            },
            legend: {
                orient: 'vertical',
                right: 10,
                top: 'center',
                textStyle: {
                    color: '#fff'
                },
                type: 'scroll',
                pageTextStyle: {
                    color: '#fff'
                },
                pageIconColor: '#aaa',
                pageIconInactiveColor: '#555'
            },
            series: [
                {
                    name: '物资类别分布',
                    type: 'pie',
                    radius: ['45%', '70%'],
                    center: ['40%', '50%'],
                    avoidLabelOverlap: false,
                    itemStyle: {
                        borderRadius: 8,
                        borderColor: '#03050C',
                        borderWidth: 2
                    },
                    label: {
                        show: false,
                        position: 'center'
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: 16,
                            fontWeight: 'bold',
                            color: '#fff'
                        },
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    },
                    labelLine: {
                        show: false
                    },
                    data: pieData,
                    color: [
                        '#00fdfa', '#fac858', '#ee6666', '#73c0de', '#91cc75',
                        '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#5470c6'
                    ]
                }
            ]
        };

        pieChart.setOption(option);
    }
};

// 返回列表页
const goBack = () => {
    router.push('/management/hospitals');
};

// 查看所有库存批次
const viewAllBatches = () => {
    router.push({ path: '/management/inventory', query: { hospital_id: hospitalId } });
};

// 查看所有预警
const viewAllAlerts = () => {
    router.push({ path: '/management/alerts', query: { hospital_id: hospitalId } });
};

// 获取预警类型样式
const getAlertTypeClass = (type: string): 'danger' | 'warning' | 'info' | 'success' | 'primary' => {
    switch (type) {
        case 'LS': return 'warning';
        case 'EX': return 'info';
        case 'ED': return 'danger';
        case 'CP': return 'warning';
        default: return 'primary';
    }
};

// 格式化日期
const formatDate = (dateStr: string | null | undefined): string => {
    if (!dateStr) return '-';
    try {
        return dayjs(dateStr).format('YYYY-MM-DD HH:mm');
    } catch {
        return '-';
    }
};

// 跳转到预警详情页
const goToAlertDetail = (alertId: string) => {
    router.push(`/management/alerts/${alertId}`);
};

const resizeChart = () => {
    pieChart?.resize();
};

onMounted(() => {
    fetchHospitalDetail();
    fetchInventoryBatches();
    fetchAlerts();

    window.addEventListener('resize', resizeChart);
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', resizeChart);
    pieChart?.dispose();
});
</script>

<template>
    <div class="hospital-detail">
        <!-- 返回按钮 -->
        <div class="back-button">
            <el-button @click="goBack">
                <el-icon>
                    <ArrowLeft />
                </el-icon>
                返回列表
            </el-button>
        </div>

        <!-- 医院信息 -->
        <div class="info-section card-style" v-loading="loading.hospital">
            <template v-if="hospital">
                <h2 class="hospital-name">{{ hospital.name }}</h2>
                <div class="hospital-info">
                    <div class="info-item">
                        <span class="label">医院等级:</span>
                        <span class="value">{{ hospital.level_display || '-' }}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">所属地区:</span>
                        <span class="value">{{ hospital.region || '-' }}</span>
                    </div>
                    <div class="info-item full-row">
                        <span class="label">详细地址:</span>
                        <span class="value">{{ hospital.address || '-' }}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">机构编码:</span>
                        <span class="value">{{ hospital.org_code || '-' }}</span>
                    </div>
                    <div class="info-item">
                        <span class="label">状态:</span>
                        <span class="value">
                            <el-tag :type="hospital.is_active ? 'success' : 'danger'" size="small">
                                {{ hospital.is_active ? '启用' : '禁用' }}
                            </el-tag>
                        </span>
                    </div>
                </div>
            </template>
            <el-empty v-else-if="!loading.hospital" description="未找到医院信息" />
        </div>

        <!-- 容量信息 -->
        <div class="capacity-section card-style" v-loading="loading.hospital">
            <template v-if="hospital && hospital.storage_volume > 0">
                <h3>库存容量概览</h3>
                <div class="capacity-info">
                    <div class="capacity-item">
                        <div class="capacity-value">{{ hospital.storage_volume?.toLocaleString() || '0' }}</div>
                        <div class="capacity-label">总容量</div>
                    </div>
                    <div class="capacity-item">
                        <div class="capacity-value">{{ hospital.current_capacity?.toLocaleString() || '0' }}</div>
                        <div class="capacity-label">当前库存</div>
                    </div>
                    <div class="capacity-item">
                        <div class="capacity-value" :style="{ color: capacityStatusColor }">
                            {{ capacityUsage }}%
                        </div>
                        <div class="capacity-label">使用率</div>
                    </div>
                    <div class="capacity-item">
                        <div class="capacity-value">{{ hospital.warning_threshold || 20 }}%</div>
                        <div class="capacity-label">预警阈值</div>
                    </div>
                </div>
                <el-progress :percentage="capacityUsage" :color="capacityStatusColor" :stroke-width="15"
                    :show-text="false" />
            </template>
            <el-empty v-else-if="!loading.hospital" description="无容量信息或总容量为0" />
        </div>

        <div class="detail-row">
            <!-- 物资分布 -->
            <div class="detail-card card-style">
                <div class="card-header">
                    <h3>库存物资类别分布</h3>
                    <el-button link type="primary" @click="viewAllBatches">查看完整库存</el-button>
                </div>
                <div v-loading="loading.inventory" class="card-body chart-container">
                    <div ref="pieChartRef" class="pie-chart"></div>
                    <el-empty v-if="!loading.inventory && inventoryBatches.length === 0" description="暂无库存数据"
                        :image-size="100" />
                </div>
            </div>

            <!-- 最近预警 -->
            <div class="detail-card card-style">
                <div class="card-header">
                    <h3>最近未解决预警</h3>
                    <el-button link type="primary" @click="viewAllAlerts">查看所有预警</el-button>
                </div>
                <div v-loading="loading.alerts" class="card-body alert-body">
                    <el-empty v-if="!loading.alerts && alerts.length === 0" description="暂无未解决预警" :image-size="100" />
                    <div v-else class="alert-list">
                        <div v-for="alert in alerts" :key="alert.alert_id" class="alert-item"
                            @click="goToAlertDetail(alert.alert_id)">
                            <el-tag :type="getAlertTypeClass(alert.alert_type)" size="small" class="alert-tag">
                                {{ alert.alert_type_display || alert.alert_type }}
                            </el-tag>
                            <div class="alert-content">
                                <span class="alert-message" :title="alert.message">{{ alert.message }}</span>
                                <span class="alert-time">{{ formatDate(alert.created_at) }}</span>
                            </div>
                            <span v-if="alert.supply?.name" class="alert-supply" :title="alert.supply.name">
                                <el-icon>
                                    <InfoFilled />
                                </el-icon> {{ alert.supply.name }}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped lang="scss">
.card-style {
    background: rgba(0, 20, 45, 0.7);
    border: 1px solid rgba(0, 180, 220, 0.3);
    border-radius: 4px;
    padding: 20px;
    margin-bottom: 20px;
    color: #fff;
}

.hospital-detail {
    padding: 20px;
    height: calc(100vh - 60px);
    overflow-y: auto;

    .back-button {
        margin-bottom: 20px;
    }

    .info-section {
        .hospital-name {
            color: #00fdfa;
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 22px;
            font-weight: bold;
        }

        .hospital-info {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px 25px;

            .info-item {
                display: flex;
                align-items: baseline;

                .label {
                    width: 80px;
                    color: rgba(255, 255, 255, 0.7);
                    flex-shrink: 0;
                    font-size: 14px;
                    text-align: right;
                    margin-right: 10px;
                }

                .value {
                    flex: 1;
                    word-break: break-word;
                    font-size: 14px;
                    color: #eee;

                    .el-tag {
                        margin-left: 5px;
                    }
                }

                &.full-row {
                    grid-column: 1 / -1;
                }
            }
        }
    }

    .capacity-section {
        h3 {
            color: #00fdfa;
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 18px;
        }

        .capacity-info {
            display: flex;
            justify-content: space-around;
            margin-bottom: 25px;
            flex-wrap: wrap;

            .capacity-item {
                text-align: center;
                padding: 10px 15px;
                min-width: 100px;

                .capacity-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #fff;
                    margin-bottom: 8px;
                    line-height: 1.2;
                }

                .capacity-label {
                    font-size: 13px;
                    color: rgba(255, 255, 255, 0.7);
                }
            }
        }

        .el-progress {
            margin-top: 10px;
        }
    }

    .detail-row {
        display: flex;
        gap: 20px;
        margin-bottom: 20px;
        flex-wrap: wrap;

        .detail-card {
            flex: 1;
            min-width: 400px;
            display: flex;
            flex-direction: column;

            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                flex-shrink: 0;

                h3 {
                    color: #00fdfa;
                    margin: 0;
                    font-size: 18px;
                }
            }

            .card-body {
                flex-grow: 1;
                min-height: 300px;
                position: relative;

                &.chart-container {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }

                .pie-chart {
                    width: 100%;
                    height: 100%;
                    min-height: 300px;
                }

                &.alert-body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }

                .alert-list {
                    width: 100%;
                    max-height: 300px;
                    overflow-y: auto;
                    padding-right: 5px;

                    .alert-item {
                        display: flex;
                        align-items: center;
                        padding: 10px 5px;
                        border-bottom: 1px solid rgba(0, 180, 220, 0.1);
                        cursor: pointer;
                        transition: background-color 0.2s;

                        &:hover {
                            background-color: rgba(0, 180, 220, 0.1);
                        }

                        &:last-child {
                            border-bottom: none;
                        }

                        .alert-tag {
                            flex-shrink: 0;
                            margin-right: 10px;
                            width: 80px;
                            text-align: center;
                        }

                        .alert-content {
                            flex-grow: 1;
                            display: flex;
                            flex-direction: column;
                            overflow: hidden;

                            .alert-message {
                                font-size: 14px;
                                color: #eee;
                                white-space: nowrap;
                                overflow: hidden;
                                text-overflow: ellipsis;
                                margin-bottom: 4px;
                            }

                            .alert-time {
                                font-size: 12px;
                                color: rgba(255, 255, 255, 0.6);
                            }
                        }

                        .alert-supply {
                            flex-shrink: 0;
                            margin-left: 15px;
                            font-size: 13px;
                            color: rgba(255, 255, 255, 0.7);
                            white-space: nowrap;
                            overflow: hidden;
                            text-overflow: ellipsis;
                            max-width: 150px;
                            display: inline-flex;
                            align-items: center;

                            .el-icon {
                                margin-right: 4px;
                            }
                        }
                    }
                }

                .el-empty {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    width: 100%;
                }
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
</style>
