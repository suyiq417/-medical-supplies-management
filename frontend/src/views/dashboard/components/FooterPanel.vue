<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'; // Import computed and onUnmounted

// Define props with type safety
const props = defineProps<{
    overviewData?: {
        hospitals: { total: number; active: number; total_capacity?: number }; // Added optional total_capacity
        supplies: { total: number; controlled: number; lowStock: number };
        alerts: { total: number; unresolved: number };
        requests: { total: number; emergency: number; pending: number };
    }
}>();

// 获取当前时间
const getCurrentTime = () => {
    const now = new Date();
    return now.toLocaleTimeString();
};

// 模拟实时数据，在实际项目中可以使用WebSocket等方式获取
const currentTime = ref(getCurrentTime());

// 更新当前时间
const intervalId = setInterval(() => {
    currentTime.value = getCurrentTime();
}, 1000);

// Clear interval on unmount (important!)
onUnmounted(() => {
    clearInterval(intervalId);
});

// Use computed properties for cleaner template access and default values
const totalHospitals = computed(() => props.overviewData?.hospitals?.total || 0);
const totalCapacity = computed(() => props.overviewData?.hospitals?.total_capacity || 0); // Assuming API might provide this
const unresolvedAlerts = computed(() => props.overviewData?.alerts?.unresolved || 0);
const pendingRequests = computed(() => props.overviewData?.requests?.pending || 0);

</script>

<template>
    <div class="footer-panel">
        <div class="system-info">
            <div class="info-item">系统版本: v2.0.0</div>
            <div class="info-item">数据更新时间: {{ currentTime }}</div>
        </div>

        <div class="summary-stats">
            <div class="stat-item">
                <span class="label">医院总数:</span>
                <!-- Use computed properties -->
                <span class="value">{{ totalHospitals }}</span>
            </div>
            <div class="stat-item">
                <span class="label">总容量:</span>
                <!-- Use computed properties -->
                <span class="value">{{ totalCapacity }}</span> <!-- Make sure API provides this or remove -->
            </div>
            <div class="stat-item">
                <span class="label">未处理预警:</span> <!-- Changed label for clarity -->
                <!-- Use computed properties -->
                <span class="value alert">{{ unresolvedAlerts }}</span>
            </div>
            <div class="stat-item">
                <span class="label">待处理请求:</span>
                <!-- Use computed properties -->
                <span class="value pending">{{ pendingRequests }}</span>
            </div>
        </div>

        <div class="copyright">
            © 2025 武汉市应急物资管理平台 <!-- Updated year -->
        </div>
    </div>
</template>

<style scoped lang="scss">
.footer-panel {
    height: 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
    background: rgba(0, 20, 45, 0.7);
    border-top: 1px solid rgba(0, 180, 220, 0.3);
    flex-shrink: 0; // Prevent shrinking

    .system-info,
    .summary-stats,
    .copyright {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.7);
    }

    .system-info {
        .info-item {
            display: inline-block;
            margin-right: 15px;
        }
    }

    .summary-stats {
        display: flex;
        gap: 15px;

        .stat-item {
            .label {
                margin-right: 5px;
            }

            .value {
                font-weight: bold;
                color: #00fdfa;

                &.alert {
                    color: #F56C6C;
                }

                &.pending {
                    color: #E6A23C;
                }
            }
        }
    }
}
</style>
