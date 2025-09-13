<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import * as echarts from 'echarts';

const props = defineProps<{
    overviewData?: {
        hospitals: { total: number; active: number };
        supplies: { total: number; controlled: number; lowStock: number };
        alerts: { total: number; unresolved: number };
        requests: { total: number; emergency: number; pending: number };
    }
}>();

const alertsChartRef = ref<HTMLElement | null>(null);
let alertsChart: echarts.ECharts | null = null;

const totalRequests = computed(() => props.overviewData?.requests?.total || 0);
const emergencyRequests = computed(() => props.overviewData?.requests?.emergency || 0);
const pendingRequests = computed(() => props.overviewData?.requests?.pending || 0);

const alertChartData = computed(() => {
    const total = props.overviewData?.alerts?.total || 0;
    const unresolved = props.overviewData?.alerts?.unresolved || 0;
    const resolved = total - unresolved;
    const safeResolved = Math.max(0, resolved);
    const safeUnresolved = Math.max(0, unresolved);

    const data = [];
    if (safeUnresolved > 0) {
        data.push({ value: safeUnresolved, name: '未处理' });
    }
    if (safeResolved > 0) {
        data.push({ value: safeResolved, name: '已处理' });
    }
    if (data.length === 0 && total === 0) {
        data.push({ value: 0, name: '无预警' });
    }
    return data;
});

const initOrUpdateAlertsChart = () => {
    if (!alertsChartRef.value) return;

    if (!alertsChart) {
        alertsChart = echarts.init(alertsChartRef.value);
    }

    const option = {
        color: ['#F56C6C', '#67C23A', '#E6A23C', '#409EFF'],
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            right: 10,
            top: 'center',
            textStyle: {
                color: '#fff'
            },
            data: alertChartData.value.map(item => item.name)
        },
        series: [
            {
                name: '预警状态',
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 5,
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
                        fontSize: 14,
                        fontWeight: 'bold',
                        formatter: '{b}\n{c}'
                    }
                },
                labelLine: {
                    show: false
                },
                data: alertChartData.value
            }
        ]
    };

    alertsChart.setOption(option, true);
};

watch(() => props.overviewData, (newData) => {
    if (newData && alertsChart) {
        initOrUpdateAlertsChart();
        alertsChart.resize();
    }
}, { deep: true });

onMounted(() => {
    initOrUpdateAlertsChart();
    window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
    window.removeEventListener('resize', handleResize);
    alertsChart?.dispose();
});

const handleResize = () => {
    alertsChart?.resize();
};
</script>

<template>
    <div class="right-panel">
        <div class="panel-block">
            <div class="block-title">预警状态分布</div>
            <div ref="alertsChartRef" class="chart"></div>
        </div>

        <div class="panel-block">
            <div class="block-title">请求处理状态</div>
            <div class="request-stats-content">
                <div class="stats-wrapper">
                    <div class="stat-card">
                        <div class="stat-value">{{ totalRequests }}</div>
                        <div class="stat-label">请求总数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value pending">{{ pendingRequests }}</div>
                        <div class="stat-label">待处理</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value emergency">{{ emergencyRequests }}</div>
                        <div class="stat-label">紧急</div>
                    </div>
                </div>
                <div class="pending-progress" v-if="totalRequests > 0">
                    <div class="progress-label">待处理占比: {{ totalRequests > 0 ? ((pendingRequests / totalRequests) *
                        100).toFixed(1) : 0 }}%</div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill"
                            :style="{ width: `${totalRequests > 0 ? (pendingRequests / totalRequests) * 100 : 0}%` }">
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped lang="scss">
.right-panel {
    display: flex;
    flex-direction: column;
    gap: 10px;
    height: 100%;

    .panel-block {
        flex: 1;
        background: rgba(0, 20, 45, 0.7);
        border: 1px solid rgba(0, 180, 220, 0.3);
        border-radius: 4px;
        padding: 10px;
        display: flex;
        flex-direction: column;

        .block-title {
            font-size: 16px;
            color: #00fdfa;
            margin-bottom: 10px;
            text-align: center;
            flex-shrink: 0;
        }

        .chart {
            width: 100%;
            flex-grow: 1;
            min-height: 100px;
        }

        .request-stats-content {
            width: 100%;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;

            .stats-wrapper {
                display: flex;
                justify-content: space-around;
                width: 100%;
                margin-bottom: 15px;

                .stat-card {
                    text-align: center;

                    .stat-value {
                        font-size: 28px;
                        font-weight: bold;
                        color: #00fdfa;
                        margin-bottom: 5px;

                        &.emergency {
                            color: #F56C6C;
                        }

                        &.pending {
                            color: #E6A23C;
                        }
                    }

                    .stat-label {
                        color: rgba(255, 255, 255, 0.7);
                        font-size: 14px;
                    }
                }
            }

            .pending-progress {
                width: 80%;
                text-align: center;

                .progress-label {
                    font-size: 12px;
                    color: rgba(255, 255, 255, 0.7);
                    margin-bottom: 5px;
                }

                .progress-bar-bg {
                    height: 8px;
                    background-color: rgba(255, 255, 255, 0.2);
                    border-radius: 4px;
                    overflow: hidden;
                }

                .progress-bar-fill {
                    height: 100%;
                    background-color: #E6A23C;
                    border-radius: 4px;
                    transition: width 0.5s ease;
                }
            }
        }
    }
}
</style>
