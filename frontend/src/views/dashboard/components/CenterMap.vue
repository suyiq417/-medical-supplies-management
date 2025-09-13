<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'; // Import nextTick
import { useRouter } from 'vue-router';
import type { Hospital } from '@/types/models';
import { ElMessage, ElIcon } from 'element-plus'; // Import ElIcon
import { Location } from '@element-plus/icons-vue'; // Removed ZoomIn as it's not used for controls now

// Declare BMapGL type (as in the reference file)
declare const BMapGL: any;
declare const BMAP_STATUS_SUCCESS: any; // For Boundary check
// Declare NavigationControl type if needed, or use 'any'
declare const BMAP_ANCHOR_TOP_RIGHT: any; // Anchor position constant

// Extend Window interface for Baidu Map callback
declare global {
    interface Window {
        onBMapGLLoaded?: () => void;
    }
}

// Props definition using defineProps with type
const props = defineProps<{
    mapData: Hospital[]
}>();

// Router instance for navigation
const router = useRouter();

// Refs for map container, map instance, loading state, and markers
const mapContainer = ref<HTMLElement | null>(null);
const mapInstance = ref<any>(null);
const mapLoading = ref(true);
const markers = ref<any[]>([]); // Store map markers (BMapGL.Marker instances)
const hospitalPoints = ref<any[]>([]); // Store BMapGL.Point instances for setViewport

const mapStyle = {
    styleJson: [
        { featureType: "background", elementType: "geometry", stylers: { color: "#03050c" } },
        { featureType: "land", elementType: "all", stylers: { color: "#071325" } },
        { featureType: "water", elementType: "all", stylers: { color: "#041832" } },
        { featureType: "boundary", elementType: "geometry", stylers: { color: "#1a5f8e" } },
        { featureType: "highway", elementType: "geometry.fill", stylers: { color: "#0a203d" } },
        { featureType: "highway", elementType: "geometry.stroke", stylers: { color: "#103a6b" } },
        { featureType: "arterial", elementType: "geometry.fill", stylers: { color: "#081c33" } },
        { featureType: "arterial", elementType: "geometry.stroke", stylers: { color: "#0d2f5f" } },
        { featureType: "local", elementType: "geometry.fill", stylers: { color: "#051529" } },
        { featureType: "local", elementType: "geometry.stroke", stylers: { visibility: "off" } },
        { featureType: "building", elementType: "geometry", stylers: { color: "#062540" } },
        { featureType: "green", elementType: "geometry", stylers: { color: "#051f3a" } },
        { featureType: "administrative", elementType: "labels", stylers: { visibility: "on" } },
        { featureType: "administrative", elementType: "labels.text.fill", stylers: { color: "#00eaff" } },
        { featureType: "administrative", elementType: "labels.text.stroke", stylers: { color: "#03050c", weight: "1.5" } },
        { featureType: "highway", elementType: "labels", stylers: { visibility: "off" } },
        { featureType: "arterial", elementType: "labels", stylers: { visibility: "off" } },
        { featureType: "local", elementType: "labels", stylers: { visibility: "off" } },
        { featureType: "railway", elementType: "all", stylers: { visibility: "off" } },
        { featureType: "subway", elementType: "all", stylers: { visibility: "off" } },
        { featureType: "poi", elementType: "all", stylers: { visibility: "off" } },
        { featureType: "manmade", elementType: "all", stylers: { visibility: "off" } },
        { featureType: "label", elementType: "all", stylers: { visibility: "off" } }
    ]
};

// Function to initialize Baidu Map
const initBaiduMap = async () => {
    mapLoading.value = true;
    if (!mapContainer.value) {
        console.error("Map container not found.");
        mapLoading.value = false;
        return;
    }

    try {
        if (typeof BMapGL === 'undefined' || !BMapGL.Map) {
            await new Promise<void>((resolve, reject) => {
                const timeout = setTimeout(() => reject(new Error('Baidu Map SDK load timeout')), 5000);
                window.onBMapGLLoaded = () => {
                    clearTimeout(timeout);
                    console.log("Baidu Map SDK loaded via callback.");
                    resolve();
                };
                if (typeof BMapGL !== 'undefined' && BMapGL.Map) {
                    clearTimeout(timeout);
                    resolve();
                }
            });
        }
        if (typeof BMapGL === 'undefined' || !BMapGL.Map) {
            throw new Error('Baidu Map SDK failed to load.');
        }

        // Create map instance
        mapInstance.value = new BMapGL.Map(mapContainer.value, {
            enableMapClick: false
        });

        // Set map center (Wuhan) and zoom level
        const point = new BMapGL.Point(114.3162, 30.5813);
        mapInstance.value.centerAndZoom(point, 11);

        // Enable scroll wheel zoom
        mapInstance.value.enableScrollWheelZoom(true);

        // Apply custom map style
        mapInstance.value.setMapStyleV2(mapStyle);

        // Add markers based on initial props.mapData
        addMarkers(props.mapData);

        // Fit viewport after initial markers are added
        await nextTick();
        fitMapToMarkers();

    } catch (error: any) {
        console.error("Failed to initialize Baidu Map:", error);
        ElMessage.error(`初始化地图失败: ${error.message || '未知错误'}`);
    } finally {
        mapLoading.value = false;
    }
};

// Function to add hospital markers to the map
const addMarkers = (hospitals: Hospital[]) => {
    if (!mapInstance.value) {
        console.error("Map instance not initialized. Cannot add markers.");
        return;
    }
    clearMarkers();
    hospitalPoints.value = [];

    if (!hospitals || hospitals.length === 0) {
        console.warn("No hospital data provided to addMarkers.");
        return;
    }

    hospitals.forEach((hospital) => {
        if (!hospital.geo_location?.coordinates || hospital.geo_location.coordinates.length !== 2) {
            console.warn(`Hospital ${hospital.name} skipped due to missing or invalid coordinates.`);
            return;
        }
        const [longitude, latitude] = hospital.geo_location.coordinates;
        if (typeof longitude !== 'number' || typeof latitude !== 'number' || isNaN(longitude) || isNaN(latitude)) {
            console.warn(`Hospital ${hospital.name} skipped due to invalid coordinate values (${longitude}, ${latitude}).`);
            return;
        }

        try {
            const hospitalPoint = new BMapGL.Point(longitude, latitude);
            hospitalPoints.value.push(hospitalPoint);

            const marker = new BMapGL.Marker(hospitalPoint);
            markers.value.push(marker);

            const levelDisplay = hospital.level_display || '未知等级';
            const address = hospital.address || '地址未提供';
            const usageRatio = hospital.usage_ratio;
            const alertsCount = hospital.alerts_count;
            let usageHtml = '';
            if (typeof usageRatio === 'number') {
                usageHtml = `<div class="tooltip-item"><span class="label">使用率:</span><span style="color:${getUsageRateColor(usageRatio)}; font-weight:bold">${usageRatio.toFixed(1)}%</span></div>`;
            }
            let alertsHtml = '';
            if (typeof alertsCount === 'number' && alertsCount > 0) {
                alertsHtml = `<div class="tooltip-item"><span class="label">预警:</span><span style="color:#ff4559; font-weight:bold">${alertsCount}个</span></div>`;
            }
            const infoWindowContent = `<div class="map-tooltip"><div class="tooltip-title">${hospital.name}</div><div class="tooltip-item"><span class="label">等级:</span> ${levelDisplay}</div><div class="tooltip-item"><span class="label">地址:</span> ${address}</div>${usageHtml}${alertsHtml}<div class="tooltip-footer">点击查看详情</div></div>`;
            const infoWindow = new BMapGL.InfoWindow(infoWindowContent, { width: 230, height: 0, offset: new BMapGL.Size(0, -15), enableMessage: false });

            marker.addEventListener('mouseover', () => { mapInstance.value.openInfoWindow(infoWindow, hospitalPoint); });
            marker.addEventListener('mouseout', () => { setTimeout(() => { if (mapInstance.value) { mapInstance.value.closeInfoWindow(); } }, 100); });
            marker.addEventListener('click', () => { router.push({ name: 'management-hospital-detail', params: { id: hospital.hospital_id } }); });

            mapInstance.value.addOverlay(marker);

        } catch (markerError) {
            console.error(`Error creating or adding marker for hospital ${hospital.name}:`, markerError);
        }
    });

    nextTick(() => {
        fitMapToMarkers();
    });
};

// Function to clear all markers from the map
const clearMarkers = () => {
    if (mapInstance.value && markers.value.length > 0) {
        markers.value.forEach(marker => {
            mapInstance.value.removeOverlay(marker);
        });
        markers.value = [];
        hospitalPoints.value = [];
    }
};

// Function to fit map viewport to markers
const fitMapToMarkers = () => {
    if (mapInstance.value && hospitalPoints.value.length > 0) {
        mapInstance.value.setViewport(hospitalPoints.value, {
            margins: [40, 20, 20, 20]
        });
    } else if (mapInstance.value && hospitalPoints.value.length === 0) {
        const defaultPoint = new BMapGL.Point(114.3162, 30.5813);
        mapInstance.value.centerAndZoom(defaultPoint, 11);
    }
};

// Helper function to determine color based on usage rate
const getUsageRateColor = (rate: number): string => {
    if (rate >= 90) return '#ff4559';
    if (rate >= 70) return '#ffab2e';
    return '#38f6b8';
};

// Handle window resize
const handleResize = () => {
    if (mapInstance.value) {
        mapInstance.value.checkResize?.();
    }
};

// Watch for changes in mapData prop
watch(() => props.mapData, (newHospitals) => {
    if (mapInstance.value) {
        console.log("Map data updated, refreshing markers...");
        addMarkers(newHospitals);
    }
}, { deep: true });

// Lifecycle Hooks
onMounted(() => {
    setTimeout(initBaiduMap, 150);
    window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
    window.removeEventListener('resize', handleResize);
    clearMarkers();
    if (mapInstance.value) {
        mapInstance.value = null;
    }
});

</script>

<template>
    <div class="center-map">
        <div class="map-title">武汉市医院分布及物资状态</div>
        <div class="map-container-wrapper">
            <!-- Loading Indicator -->
            <div class="map-loading" v-if="mapLoading">
                <el-icon class="is-loading" :size="24">
                    <Loading />
                </el-icon>
                <span>地图加载中...</span>
            </div>
            <!-- Map Container -->
            <div ref="mapContainer" class="map-container" :style="{ visibility: mapLoading ? 'hidden' : 'visible' }">
            </div>
        </div>
    </div>
</template>

<style scoped lang="scss">
.center-map {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: rgba(0, 20, 45, 0.7);
    border: 1px solid rgba(0, 180, 220, 0.3);
    border-radius: 4px;
    padding: 10px;
    box-sizing: border-box;

    .map-title {
        font-size: 20px;
        color: #00fdfa;
        margin-bottom: 10px;
        text-align: center;
        flex-shrink: 0;
        text-shadow: 0 0 5px rgba(0, 234, 255, 0.5);
    }

    .map-container-wrapper {
        flex: 1;
        position: relative;
        min-height: 0;
        border-radius: 4px;
        overflow: hidden;

        .map-container {
            width: 100%;
            height: 100%;
        }

        .map-loading {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 10;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background-color: rgba(3, 5, 12, 0.85);
            color: #fff;
            border-radius: 4px;

            .el-icon {
                margin-bottom: 10px;
                color: #00eaff;
            }

            span {
                font-size: 14px;
            }
        }

        .fit-bounds-btn {
            position: absolute;
            top: 50px;
            right: 10px;
            z-index: 5;
            background-color: rgba(25, 45, 75, 0.8);
            border: 1px solid rgba(0, 180, 220, 0.5);
            color: #00eaff;
            padding: 5px;
            border-radius: 3px;
            cursor: pointer;
            transition: background-color 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;

            &:hover {
                background-color: rgba(35, 65, 105, 0.9);
                border-color: rgba(0, 180, 220, 0.8);
            }

            .el-icon {
                vertical-align: middle;
            }
        }
    }
}

:deep(.BMap_bubble_pop) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

:deep(.BMap_bubble_top),
:deep(.BMap_bubble_bottom),
:deep(.BMap_bubble_center),
:deep(.BMap_bubble_content > div:not(.map-tooltip)) {
    background: transparent !important;
    border: none !important;
}

:deep(.BMap_bubble_content) {
    background-color: rgba(0, 10, 30, 0.9) !important;
    border: 1px solid rgba(0, 180, 220, 0.6) !important;
    border-radius: 4px !important;
    padding: 10px 12px !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5) !important;
    color: #fff !important;
    width: auto !important;
    height: auto !important;
}

:deep(.BMap_bubble_pop > img),
:deep(.BMap_pop > img[src*="close"]),
:deep(.BMap_bubble_close),
:deep(.BMap_shadow) {
    display: none !important;
    opacity: 0 !important;
    visibility: hidden !important;
}

:deep(.map-tooltip) {
    .tooltip-title {
        font-size: 14px;
        font-weight: bold;
        color: #00eaff;
        margin-bottom: 8px;
        text-align: center;
        border-bottom: 1px solid rgba(0, 180, 220, 0.4);
        padding-bottom: 5px;
        white-space: nowrap;
    }

    .tooltip-item {
        margin: 6px 0;
        font-size: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        line-height: 1.4;

        .label {
            color: rgba(255, 255, 255, 0.7);
            margin-right: 8px;
            flex-shrink: 0;
        }

        span:last-child {
            text-align: right;
            word-break: break-all;
        }
    }

    .tooltip-footer {
        margin-top: 8px;
        font-size: 11px;
        color: #00eaff;
        text-align: center;
        border-top: 1px solid rgba(0, 180, 220, 0.4);
        padding-top: 5px;
    }
}

:deep(.BMap_stdMpCtrl) {}

:deep(.BMap_stdMpZoom) {
    background-color: rgba(25, 45, 75, 0.8) !important;
    border: 1px solid rgba(0, 180, 220, 0.5) !important;
    border-radius: 3px !important;
    overflow: hidden;

    span {
        background-color: transparent !important;
        color: #00eaff !important;

        &.BMap_stdMpZoomIn {
            border-bottom: 1px solid rgba(0, 180, 220, 0.5) !important;
        }

        &.BMap_stdMpZoomOut {}

        &:hover {
            background-color: rgba(35, 65, 105, 0.9) !important;
        }
    }
}

:deep(.BMap_stdMpType),
:deep(.BMap_stdMpPan) {
    display: none !important;
}
</style>
