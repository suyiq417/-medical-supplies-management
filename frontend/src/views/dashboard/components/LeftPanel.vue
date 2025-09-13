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

const supplyChartRef = ref<HTMLElement | null>(null);
let supplyChart: echarts.ECharts | null = null;

const totalHospitals = computed(() => props.overviewData?.hospitals?.total || 0);
const activeHospitals = computed(() => props.overviewData?.hospitals?.active || 0);

const supplyChartData = computed(() => {
    const total = props.overviewData?.supplies?.total || 0;
    const controlled = props.overviewData?.supplies?.controlled || 0;
    const lowStock = props.overviewData?.supplies?.lowStock || 0;
    const other = total - controlled - lowStock;
    const safeOther = Math.max(0, other);

    const data = [];
    if (controlled > 0) data.push({ value: controlled, name: '管制物资' });
    if (lowStock > 0) data.push({ value: lowStock, name: '低库存' });
    if (safeOther > 0) data.push({ value: safeOther, name: '正常库存' });

    if (data.length === 0 && total === 0) {
        data.push({ value: 0, name: '无物资数据' });
    }

    return data;
});

const initOrUpdateSupplyChart = () => {
    if (!supplyChartRef.value) return;

    if (!supplyChart) {
        supplyChart = echarts.init(supplyChartRef.value);
    }

    const option = {
        color: ['#E6A23C', '#F56C6C', '#67C23A', '#409EFF'],
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            bottom: 10,
            left: 'center',
            textStyle: {
                color: '#fff'
            },
            data: supplyChartData.value.map(item => item.name)
        },
        series: [
            {
                name: '物资状态',
                type: 'pie',
                radius: ['30%', '60%'],
                center: ['50%', '45%'],
                avoidLabelOverlap: true,
                itemStyle: {
                    borderRadius: 5,
                    borderColor: '#03050C',
                    borderWidth: 2
                },
                label: {
                    show: true,
                    position: 'outside',
                    formatter: '{b}: {d}%',
                    color: '#fff',
                    fontSize: 12
                },
                labelLine: {
                    show: true,
                    length: 8,
                    length2: 10,
                    lineStyle: {
                        color: '#fff'
                    }
                },
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                },
                data: supplyChartData.value
            }
        ]
    };

    supplyChart.setOption(option, true);
};

watch(() => props.overviewData, (newData) => {
    if (newData) {
        initOrUpdateSupplyChart();
        if (supplyChart) {
            supplyChart.resize();
        }
    }
}, { deep: true });

onMounted(() => {
    initOrUpdateSupplyChart();
    window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
    window.removeEventListener('resize', handleResize);
    supplyChart?.dispose();
});

const handleResize = () => {
    supplyChart?.resize();
};
</script>

<template>
    <div class="left-panel">
        <div class="panel-block">
            <div class="block-title">物资状态统计</div>
            <div ref="supplyChartRef" class="chart"></div>
        </div>

        <div class="panel-block">
            <div class="block-title">医院运行指标</div>
            <div class="hospital-metrics-content">
                <div class="metric-item">
                    <div class="metric-value">{{ totalHospitals }}</div>
                    <div class="metric-label">医院总数</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value active">{{ activeHospitals }}</div>
                    <div class="metric-label">活跃医院</div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped lang="scss">
.left-panel {
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

        .hospital-metrics-content {
            width: 100%;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 20px;

            .metric-item {
                text-align: center;

                .metric-value {
                    font-size: 36px;
                    font-weight: bold;
                    color: #00fdfa;
                    margin-bottom: 8px;

                    &.active {
                        color: #67C23A;
                    }
                }

                .metric-label {
                    color: rgba(255, 255, 255, 0.7);
                    font-size: 14px;
                }
            }
        }
    }
}
</style>
