<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from "vue";
import BorderBox13 from "@/components/datav/border-box-13";
import { hospitalsMap } from "@/api/modules/index";
import { ElMessage } from "element-plus";
import { useSettingStore } from "@/stores";
import { storeToRefs } from "pinia";

// 声明 BMapGL
declare const BMapGL: any;

// 扩展 Window 接口以包含百度地图的回调
declare global {
  interface Window {
    onBMapGLLoaded?: () => void;
  }
}

// 定义事件
const emit = defineEmits(['select-hospital']);

// 地图实例和容器
const mapInstance = ref<any>(null);
const mapContainer = ref<HTMLElement | null>(null);
const mapLoading = ref(true);

// 地图配置
const settingStore = useSettingStore();
const { indexConfig } = storeToRefs(settingStore);

// 医院数据
const hospitals = ref<any[]>([]);
const markers = ref<any[]>([]); // 存储地图上的标记
const hospitalPoints = ref<any[]>([]); // 存储医院的坐标点

// 自定义地图样式 (隐藏大部分 POI 和道路名称，保留行政区名称)
const mapStyle = {
  styleJson: [
    // 基础元素
    {
      "featureType": "background",
      "elementType": "geometry",
      "stylers": {
        "color": "#03050c" // 匹配页面背景色
      }
    },
    {
      "featureType": "land",
      "elementType": "all",
      "stylers": {
        "color": "#071325" // 深蓝色陆地
      }
    },
    {
      "featureType": "water",
      "elementType": "all",
      "stylers": {
        "color": "#041832" // 略深的蓝色水域
      }
    },
    // 边界和行政区
    {
      "featureType": "boundary",
      "elementType": "geometry",
      "stylers": {
        "color": "#1a5f8e" // 调整边界线颜色，更融入背景
      }
    },
    // 道路和交通 - 进一步弱化
    {
      "featureType": "highway",
      "elementType": "geometry.fill",
      "stylers": {
        "color": "#0a203d" // 更暗的高速公路填充
      }
    },
    {
      "featureType": "highway",
      "elementType": "geometry.stroke",
      "stylers": {
        "color": "#103a6b" // 更暗的高速公路描边
      }
    },
    {
      "featureType": "arterial",
      "elementType": "geometry.fill",
      "stylers": {
        "color": "#081c33" // 更暗的主干道填充
      }
    },
    {
      "featureType": "arterial",
      "elementType": "geometry.stroke",
      "stylers": {
        "color": "#0d2f5f" // 更暗的主干道描边
      }
    },
    {
      "featureType": "local",
      "elementType": "geometry.fill",
      "stylers": {
        "color": "#051529" // 最暗的地方道路填充
      }
    },
    {
      "featureType": "local",
      "elementType": "geometry.stroke",
      "stylers": {
        "visibility": "off" // 隐藏地方道路描边
      }
    },
    // 建筑物和人造物 - 进一步弱化
    {
      "featureType": "building",
      "elementType": "geometry",
      "stylers": {
        "color": "#062540" // 更暗的建筑物颜色
      }
    },
    {
      "featureType": "green",
      "elementType": "geometry",
      "stylers": {
        "color": "#051f3a" // 更暗的绿地颜色
      }
    },
    // 行政区标签 - 保持可见并使用主题色
    {
      "featureType": "administrative",
      "elementType": "labels",
      "stylers": {
        "visibility": "on"
      }
    },
    {
      "featureType": "administrative",
      "elementType": "labels.text.fill",
      "stylers": {
        "color": "#00eaff" // 使用主题高亮青色
      }
    },
    {
      "featureType": "administrative",
      "elementType": "labels.text.stroke",
      "stylers": {
        "color": "#03050c", // 使用背景色作为描边，增强融合感
        "weight": "1.5"
      }
    },
    // 隐藏所有其他元素的标签
    {
      "featureType": "highway",
      "elementType": "labels",
      "stylers": {
        "visibility": "off"
      }
    },
    {
      "featureType": "arterial",
      "elementType": "labels",
      "stylers": {
        "visibility": "off"
      }
    },
    {
      "featureType": "local",
      "elementType": "labels",
      "stylers": {
        "visibility": "off"
      }
    },
    {
      "featureType": "railway",
      "elementType": "all",
      "stylers": {
        "visibility": "off"
      }
    },
    {
      "featureType": "subway",
      "elementType": "all",
      "stylers": {
        "visibility": "off"
      }
    },
    {
      "featureType": "poi",
      "elementType": "all",
      "stylers": {
        "visibility": "off"
      }
    },
    {
      "featureType": "manmade",
      "elementType": "all",
      "stylers": {
        "visibility": "off"
      }
    },
    // 确保除行政区外的其他标签都隐藏
    {
      "featureType": "label",
      "elementType": "all",
      "stylers": {
        "visibility": "off"
      }
    }
  ]
};

// 初始化地图
const initBaiduMap = async () => {
  mapLoading.value = true;
  if (!mapContainer.value) {
    console.error("地图容器未找到");
    mapLoading.value = false;
    return;
  }

  try {
    // 确保 BMapGL 已加载
    if (typeof BMapGL === 'undefined' || !BMapGL.Map) {
      ElMessage.error('百度地图 SDK 未能成功加载');
      mapLoading.value = false;
      // 可以添加重试逻辑或提示用户刷新
      // 例如，监听 window.onBMapGLLoaded 事件
      await new Promise<void>((resolve) => {
        window.onBMapGLLoaded = () => {
          console.log("百度地图 SDK 加载完成 (回调)");
          resolve();
        };
        // 如果已经加载但未检测到，尝试再次检查
        if (typeof BMapGL !== 'undefined' && BMapGL.Map) {
          resolve();
        }
      });
      if (typeof BMapGL === 'undefined' || !BMapGL.Map) {
        ElMessage.error('百度地图 SDK 加载失败，请刷新页面重试');
        mapLoading.value = false;
        return;
      }
    }

    // 创建地图实例
    mapInstance.value = new BMapGL.Map(mapContainer.value, {
      enableMapClick: false // 禁止点击地图获取地点信息
    });

    // 设置地图中心点和缩放级别 (武汉)
    const point = new BMapGL.Point(114.3162, 30.5813);
    mapInstance.value.centerAndZoom(point, 12);

    // 启用滚轮缩放
    mapInstance.value.enableScrollWheelZoom(true);

    // 直接应用自定义的 mapStyle 样式规则
    mapInstance.value.setMapStyleV2(mapStyle);

    // 获取并添加医院标记
    await loadAndAddMarkers();

  } catch (error) {
    console.error("初始化百度地图失败:", error);
    ElMessage.error('初始化地图失败');
  } finally {
    mapLoading.value = false;
  }
};

// 加载并添加医院标记
const loadAndAddMarkers = async () => {
  if (!mapInstance.value) {
    console.error("地图实例尚未初始化，无法添加标记。");
    return;
  }
  try {
    console.log("开始加载医院标记...");
    const response = await hospitalsMap();
    console.log("医院地图 API 响应:", response); // <-- 添加日志

    if (response && Array.isArray(response) && response.length > 0) {
      hospitals.value = response;
      clearMarkers(); // 清除旧标记
      hospitalPoints.value = []; // 清除旧坐标点
      console.log(`准备添加 ${hospitals.value.length} 个医院标记。`);

      hospitals.value.forEach((hospital, index) => {
        console.log(`处理医院 #${index + 1}:`, hospital); // <-- 添加日志

        if (!hospital.geo_location || !hospital.geo_location.coordinates || hospital.geo_location.coordinates.length !== 2) {
          console.warn(`医院 ${hospital.name || '未知'} (ID: ${hospital.hospital_id}) 缺少有效坐标信息，跳过标记。`, hospital.geo_location);
          return;
        }

        const [longitude, latitude] = hospital.geo_location.coordinates;

        // 再次检查经纬度是否为有效数字
        if (typeof longitude !== 'number' || typeof latitude !== 'number' || isNaN(longitude) || isNaN(latitude)) {
          console.warn(`医院 ${hospital.name || '未知'} (ID: ${hospital.hospital_id}) 的坐标无效 (${longitude}, ${latitude})，跳过标记。`);
          return;
        }

        console.log(`医院 ${hospital.name}: 坐标 (${longitude}, ${latitude})`); // <-- 添加日志

        try {
          const hospitalPoint = new BMapGL.Point(longitude, latitude);
          hospitalPoints.value.push(hospitalPoint); // 添加到坐标点数组
          console.log(`  创建 Point 对象:`, hospitalPoint);

          // --- 恢复：使用默认标记 ---
          const marker = new BMapGL.Marker(hospitalPoint); // 不再传入 icon 或 symbol
          markers.value.push(marker);
          // --- 标记创建恢复结束 ---

          // --- 添加事件监听器 ---
          const infoWindowContent = `
            <div class="map-tooltip">
              <div class="tooltip-title">${hospital.name}</div>
              <div class="tooltip-item"><span class="label">等级:</span> ${hospital.level_display}</div>
              <div class="tooltip-item"><span class="label">区域:</span> ${hospital.region}</div>
              <div class="tooltip-item">
                <span class="label">使用率:</span>
                <span style="color:${getUsageRateColor(hospital.usage_ratio)}; font-weight:bold">
                  ${hospital.usage_ratio.toFixed(1)}%
                </span>
              </div>
              ${hospital.alerts_count > 0 ?
              `<div class="tooltip-item">
                <span class="label">预警:</span>
                <span style="color:#ff4559; font-weight:bold">${hospital.alerts_count}个</span>
              </div>` : ''}
              <div class="tooltip-footer">点击查看详情</div>
            </div>
          `;
          const infoWindow = new BMapGL.InfoWindow(infoWindowContent, {
            width: 220,
            height: 0,
            offset: new BMapGL.Size(0, -15), // 恢复或调整此值
            enableMessage: false
          });

          // 鼠标悬停时打开信息窗口
          marker.addEventListener('mouseover', () => {
            mapInstance.value.openInfoWindow(infoWindow, hospitalPoint);
          });

          // 鼠标移出时关闭信息窗口
          marker.addEventListener('mouseout', () => {
            mapInstance.value.closeInfoWindow();
          });

          // 点击事件
          marker.addEventListener('click', () => {
            emit('select-hospital', {
              id: hospital.hospital_id,
              name: hospital.name
            });
            mapInstance.value.openInfoWindow(infoWindow, hospitalPoint);
          });
          // --- 事件监听器结束 ---

          // 将标记添加到地图
          mapInstance.value.addOverlay(marker);
          console.log(`  成功添加标记到地图: ${hospital.name}`);

        } catch (markerError) {
          console.error(`为医院 ${hospital.name} 创建或添加标记时出错:`, markerError);
        }
      });
      console.log("所有有效医院标记处理完毕。");

      // 调整地图视野以适应所有标记
      fitMapToMarkers();
    } else {
      ElMessage.warning('未获取到有效的医院数据或数据为空');
      console.warn("API 返回数据无效或为空:", response);
    }
  } catch (error) {
    console.error("加载或添加医院标记过程中发生错误:", error);
    ElMessage.error('加载医院标记失败');
  }
};

// 清除地图上的所有标记
const clearMarkers = () => {
  markers.value.forEach(marker => {
    mapInstance.value.removeOverlay(marker);
  });
  markers.value = [];
};

// 获取使用率对应的颜色
const getUsageRateColor = (rate: number): string => {
  if (rate >= 90) return '#ff4559';  // 红色
  if (rate >= 70) return '#ffab2e';  // 橙色
  return '#38f6b8';                  // 绿色
};

// 调整地图视野以适应所有标记
const fitMapToMarkers = () => {
  if (!mapInstance.value || hospitalPoints.value.length === 0) {
    console.warn("无法调整地图视野：地图实例未初始化或没有标记点。");
    // 如果没有标记点，可以考虑重置到默认视图或保持当前视图
    if (mapInstance.value) {
      const defaultPoint = new BMapGL.Point(114.3162, 30.5813); // 武汉中心点
      mapInstance.value.centerAndZoom(defaultPoint, 12); // 重置到初始缩放级别
    }
    return;
  }

  // 使用 setViewport 直接传入点数组，并可以设置边距
  // 参数: points: Point[], viewportOptions?: {margins?: number[], zoomFactor?: number, delay?: number}
  mapInstance.value.setViewport(hospitalPoints.value, {
    margins: [40, 20, 20, 20] // 上、右、下、左的边距 (像素)
    // zoomFactor: -1 // 可以调整缩放因子，负数表示缩小一点以留出更多空间，默认是0
  });

  // 确保在只有一个点时不至于缩放级别过大
  if (hospitalPoints.value.length === 1) {
    mapInstance.value.setZoom(15); // 设置一个合适的固定缩放级别
  }
};

// 处理窗口大小变化 (百度地图通常自适应，但可以保留以防万一)
const handleResize = () => {
  // 百度地图 GL 版通常会自动适应容器大小，此函数可能不需要
  // if (mapInstance.value) {
  //   mapInstance.value.checkResize();
  // }
};

onMounted(() => {
  // 延迟初始化，确保DOM渲染完成且SDK可能已加载
  setTimeout(initBaiduMap, 100);
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  // 清理地图实例和事件监听器
  if (mapInstance.value) {
    // 尝试销毁地图实例，百度地图API可能没有显式destroy方法
    // mapInstance.value.destroy(); // 检查API文档确认是否有此方法
    mapInstance.value = null;
  }
  window.removeEventListener('resize', handleResize);
});

// 监听配置变化，可以用来刷新标记等（如果需要）
watch(() => indexConfig.value, (newConfig) => {
  if (newConfig && mapInstance.value) {
    console.log('配置变化，重新加载标记...');
    loadAndAddMarkers(); // 重新加载标记
  }
}, { deep: true });

withDefaults(
  defineProps<{
    title: string;
  }>(),
  {
    title: "武汉市医院分布",
  }
);
</script>

<template>
  <div class="centermap">
    <div class="maptitle">
      <div class="zuo"></div>
      <span class="titletext">{{ title }}</span>
      <div class="you"></div>
    </div>
    <div class="mapwrap">
      <BorderBox13>
        <div class="map-loading" v-if="mapLoading">
          <el-icon class="is-loading">
            <element-loading />
          </el-icon>
          <span>地图加载中...</span>
        </div>
        <!-- 修改 ID -->
        <div id="baidu-map-container" ref="mapContainer"></div>
      </BorderBox13>
    </div>
  </div>
</template>

<style scoped lang="scss">
.centermap {
  margin-bottom: 30px;
  position: relative;
  height: 100%; // 确保父容器有高度
  display: flex; // 使用 flex 布局
  flex-direction: column; // 垂直排列

  .maptitle {
    height: 60px;
    display: flex;
    justify-content: center;
    padding-top: 10px;
    box-sizing: border-box;
    flex-shrink: 0; // 防止标题被压缩

    .titletext {
      font-size: 28px;
      font-weight: 900;
      letter-spacing: 6px;
      background: linear-gradient(92deg, #0072ff 0%, #00eaff 48.8525390625%, #01aaff 100%);
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0 10px;
      text-shadow: 0 0 10px rgba(0, 234, 255, 0.5);
    }

    .zuo,
    .you {
      background-size: 100% 100%;
      width: 29px;
      height: 20px;
      margin-top: 8px;
    }

    .zuo {
      background: url("@/assets/img/xiezuo.png") no-repeat;
    }

    .you {
      background: url("@/assets/img/xieyou.png") no-repeat;
    }
  }

  .mapwrap {
    // height: calc(100% - 60px); // 减去标题高度
    flex-grow: 1; // 占据剩余空间
    width: 100%;
    box-sizing: border-box;
    position: relative;
    box-shadow: 0 0 15px rgba(0, 180, 220, 0.2);
    transition: box-shadow 0.3s ease;
    min-height: 400px; // 保证最小高度

    &:hover {
      box-shadow: 0 0 25px rgba(0, 200, 255, 0.3);
    }

    // 容器样式
    :deep(.dv-border-box-13 .border-box-content) {
      padding: 0; // 移除 datav 组件的内边距
    }

    .map-loading {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 5;
      background: rgba(0, 20, 40, 0.8);
      padding: 20px 40px;
      border-radius: 4px;
      color: #fff;
      display: flex;
      flex-direction: column;
      align-items: center;
      border: 1px solid rgba(0, 180, 220, 0.4);
      box-shadow: 0 0 15px rgba(0, 180, 220, 0.3);

      .el-icon {
        font-size: 24px;
        margin-bottom: 10px;
        color: #00eaff;
      }

      span {
        font-size: 14px;
      }
    }

    // 修改 ID 选择器
    #baidu-map-container {
      width: 100%;
      height: 100%; // 确保地图容器占满父元素
    }
  }
}

// 工具提示样式（全局注入或使用 :deep()）
:deep(.BMap_bubble_pop) {
  background: transparent !important; // 主容器透明
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
  background-color: rgba(0, 10, 30, 0.9) !important; // 强制背景色
  border: 1px solid rgba(0, 180, 220, 0.6) !important;
  border-radius: 4px !important;
  padding: 10px !important;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5) !important;
  color: #fff !important; // 默认文字颜色
}

:deep(.BMap_bubble_pop>img),
:deep(.BMap_bubble_pop img[src*="close"]),
:deep(.BMap_bubble_close),
:deep(.BMap_shadow) {
  // 隐藏默认箭头图片和关闭按钮
  display: none !important;
  opacity: 0 !important;
  visibility: hidden !important;
}

:deep(.BMap_bubble_pop>img) {
  // 隐藏默认箭头图片
  display: none;
}

// 使用 :deep() 应用样式到 InfoWindow 内容
:deep(.map-tooltip) {
  // 将 min-height 移到所有嵌套规则之前
  min-height: 100px; // 可选：添加最小高度，使窗口大小更统一

  .tooltip-title {
    font-size: 14px;
    font-weight: bold;
    color: #00eaff;
    margin-bottom: 8px;
    text-align: center;
    text-shadow: 0 0 5px rgba(0, 234, 255, 0.5);
    border-bottom: 1px solid rgba(0, 180, 220, 0.4);
    padding-bottom: 5px;
  }

  .tooltip-item {
    margin: 6px 0;
    font-size: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .label {
      color: rgba(255, 255, 255, 0.7);
      margin-right: 8px;
      flex-shrink: 0; // 防止标签被压缩
    }

    span:last-child {
      // 值部分
      word-break: break-all; // 防止长文本溢出
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

// 新增：隐藏 InfoWindow 的关闭按钮 (×)
:deep(.BMap_pop>img[src*="close"]) {
  display: none !important; // 使用 !important 确保覆盖默认样式
}
</style>
