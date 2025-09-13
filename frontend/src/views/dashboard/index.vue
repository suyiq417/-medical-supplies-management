<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import {
    hospitalsOverview,
    hospitalsMap,
    suppliesOverview,
    inventoryAlerts,
    requestStatus
} from '@/api/modules/index';
import { ElMessage } from 'element-plus';
import type { Hospital } from '@/types/models';
import LeftPanel from './components/LeftPanel.vue';
import RightPanel from './components/RightPanel.vue';
import CenterMap from './components/CenterMap.vue';
import HeaderPanel from './components/HeaderPanel.vue';
import FooterPanel from './components/FooterPanel.vue';

// 地图数据
const mapData = ref<Hospital[]>([]);
// 总览数据
const overviewData = ref({
    hospitals: { total: 0, active: 0 },
    supplies: { total: 0, controlled: 0, lowStock: 0 },
    alerts: { total: 0, unresolved: 0 },
    requests: { total: 0, emergency: 0, pending: 0 }
});
const loading = ref(true);

// 加载所有数据
const loadAllData = async () => {
    loading.value = true;
    try {
        // 并行加载所有数据
        const [hospitalsData, mapDataResult, suppliesData, alertsData, requestsData] = await Promise.all([
            hospitalsOverview(),
            hospitalsMap(),
            suppliesOverview(),
            inventoryAlerts(),
            requestStatus()
        ]);

        // 处理医院数据
        if (hospitalsData) {
            overviewData.value.hospitals.total = hospitalsData.total_hospitals;
            overviewData.value.hospitals.active = hospitalsData.active_hospitals;
        }

        // 处理地图数据
        if (mapDataResult) {
            mapData.value = mapDataResult;
        }

        // 处理物资数据
        if (suppliesData) {
            overviewData.value.supplies.total = suppliesData.total_supplies;
            overviewData.value.supplies.controlled = suppliesData.controlled_supplies;
            overviewData.value.supplies.lowStock = suppliesData.low_stock_supplies;
        }

        // 处理预警数据
        if (alertsData) {
            overviewData.value.alerts.total = alertsData.total_alerts;
            overviewData.value.alerts.unresolved = alertsData.unresolved_alerts;
        }

        // 处理请求数据
        if (requestsData) {
            overviewData.value.requests.total = requestsData.total_requests;
            overviewData.value.requests.emergency = requestsData.emergency_requests;
            overviewData.value.requests.pending = requestsData.pending_approval;
        }
    } catch (err) {
        console.error('加载数据失败', err);
        ElMessage.error('数据加载失败');
    } finally {
        loading.value = false;
    }
};

// 处理窗口调整
const handleResize = () => {
    // 可以在这里添加窗口大小变化时的处理逻辑
};

onMounted(() => {
    loadAllData();

    // 设置定时刷新
    const refreshTimer = setInterval(loadAllData, 60000); // 1分钟刷新一次

    window.addEventListener('resize', handleResize);

    onUnmounted(() => {
        clearInterval(refreshTimer);
        window.removeEventListener('resize', handleResize);
    });
});
</script>

<template>
    <div class="dashboard-container" v-loading.fullscreen="loading">
        <!-- 头部面板 -->
        <header-panel :overview-data="overviewData" />

        <div class="dashboard-content">
            <!-- 左侧面板 -->
            <left-panel :overview-data="overviewData" class="side-panel" />

            <!-- 中间地图 -->
            <center-map :map-data="mapData" class="center-area" />

            <!-- 右侧面板 -->
            <right-panel :overview-data="overviewData" class="side-panel" />
        </div>

        <!-- 底部面板 -->
        <footer-panel :overview-data="overviewData" />
    </div>
</template>

<style scoped lang="scss">
.dashboard-container {
    width: 100%;
    height: 100vh;
    background-color: #03050C;
    color: #fff;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .dashboard-content {
        flex: 1;
        display: flex;
        width: 100%;
        height: calc(100vh - 140px);

        .side-panel {
            width: 25%;
            height: 100%;
            padding: 10px;
        }

        .center-area {
            flex: 1;
            height: 100%;
            padding: 10px;
        }
    }
}
</style>
