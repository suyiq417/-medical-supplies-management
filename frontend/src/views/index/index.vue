<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import ItemWrap from "@/components/item-wrap.vue";
import LeftTop from "./left-top.vue";
import LeftCenter from "./left-center.vue";
import LeftBottom from "./left-bottom.vue";
import CenterMap from "./center-map.vue";
import CenterBottom from "./center-bottom.vue";
import RightTop from "./right-top.vue";
import RightCenter from "./right-center.vue";
import RightBottom from "./right-bottom.vue";
import { useSettingStore } from "@/stores";
import { storeToRefs } from "pinia";
import HeaderView from '../header.vue';

// 选中的医院数据
interface SelectedHospital {
  id: string;
  name: string;
}

const selectedHospital = ref('');
const selectedHospitalId = ref('');

// 获取设置
const settingStore = useSettingStore();
const { indexConfig } = storeToRefs(settingStore);

// 刷新计时器
const refreshTimers = ref<{ [key: string]: number }>({});

// 添加类型安全的日志函数
const log = (message: string, ...args: any[]) => {
  console.log(`[首页] ${message}`, ...args);
};

// 调试函数 - 确保DOM已加载
const checkDOMElements = () => {
  try {
    log('检查DOM元素');
    const container = document.querySelector('.dashboard-container');
    log('容器元素:', container);
  } catch (error) {
    log('DOM检查错误', error);
  }
};

// 处理医院选择 - 修正类型定义
const handleSelectHospital = (hospital: SelectedHospital) => {
  if (!hospital || typeof hospital !== 'object') {
    log('选中的医院数据格式错误:', hospital);
    return;
  }

  log('选中医院:', hospital);
  selectedHospitalId.value = hospital.id || '';
  selectedHospital.value = hospital.name || '';
};

// 设置各模块刷新间隔 - 增加错误处理
const setupRefreshTimers = () => {
  // 清理现有定时器
  clearRefreshTimers();

  // 创建安全的刷新间隔配置
  const refreshIntervals = {
    leftTop: indexConfig.value?.refreshInterval?.leftTop || 30,
    centerBottom: indexConfig.value?.refreshInterval?.centerBottom || 30
  };

  // 左上模块 - 物资总览定时刷新
  if (refreshIntervals.leftTop > 0) {
    const interval = refreshIntervals.leftTop * 1000;
    refreshTimers.value.leftTopTimer = window.setInterval(() => {
      log('刷新左上模块');
      // 这里可以触发一个事件通知左上组件刷新
    }, interval);
  }

  // 中下模块 - 调配趋势定时刷新
  if (refreshIntervals.centerBottom > 0) {
    const interval = refreshIntervals.centerBottom * 1000;
    refreshTimers.value.centerBottomTimer = window.setInterval(() => {
      log('刷新中下模块');
      // 这里可以触发一个事件通知中下组件刷新
    }, interval);
  }
};

// 清理定时器
const clearRefreshTimers = () => {
  Object.values(refreshTimers.value).forEach(timer => {
    clearInterval(timer);
  });
  refreshTimers.value = {};
};

// 监听设置变化，重新设置刷新间隔
watch(() => indexConfig.value, (newConfig) => {
  if (newConfig) {
    log('配置已更新，重新设置定时器');
    setupRefreshTimers();
  }
}, { deep: true });

onMounted(() => {
  log('页面挂载');

  // 确保设置已经初始化
  if (!indexConfig.value) {
    log('警告: indexConfig未初始化，使用默认值');
  }

  setupRefreshTimers();

  // 添加延迟DOM检查，确保页面渲染完成
  setTimeout(checkDOMElements, 500);
});

onBeforeUnmount(() => {
  clearRefreshTimers();
});
</script>

<template>
  <div class="dashboard-container">
    <header-view class="dashboard-header" />

    <div class="dashboard-content">
      <div class="dashboard-bg-effect"></div>
      <div class="index-box">
        <div class="contetn_left">
          <ItemWrap class="contetn_left-top contetn_lr-item" title="物资类别总览">
            <LeftTop ref="leftTopRef" />
          </ItemWrap>
          <ItemWrap class="contetn_left-center contetn_lr-item" title="医院资源概览">
            <LeftCenter />
          </ItemWrap>
          <ItemWrap class="contetn_left-bottom contetn_lr-item" title="库存预警" style="padding: 0 10px 16px 10px">
            <LeftBottom />
          </ItemWrap>
        </div>
        <div class="contetn_center">
          <CenterMap @select-hospital="handleSelectHospital" title="武汉市医院分布" class="map-container" />
          <ItemWrap class="contetn_center-bottom" title="物资请求履行计划">
            <CenterBottom ref="centerBottomRef" />
          </ItemWrap>
        </div>
        <div class="contetn_right">
          <ItemWrap class="contetn_right-top contetn_lr-item" title="医院搜索">
            <RightTop @search="handleSelectHospital" />
          </ItemWrap>
          <ItemWrap class="contetn_right-center contetn_lr-item" title="医院详情" style="padding: 0 10px 16px 10px">
            <RightCenter :hospital-id="selectedHospitalId" :hospital-name="selectedHospital" />
          </ItemWrap>
          <ItemWrap class="contetn_right-bottom contetn_lr-item" title="物资请求状态">
            <RightBottom />
          </ItemWrap>
        </div>
      </div>
    </div>
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
  position: relative;
}

.dashboard-header {
  width: 100%;
  z-index: 1000;
}

.dashboard-content {
  flex: 1;
  display: flex;
  width: 100%;
  padding: 15px;
  gap: 15px;
  position: relative;
  overflow: hidden;
}

.dashboard-bg-effect {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 70% 30%, rgba(0, 100, 200, 0.1), transparent 70%);
  pointer-events: none;
  z-index: 0;
}

.index-box {
  width: 100%;
  display: flex;
  min-height: calc(100% - 20px);
  justify-content: space-between;
  z-index: 1;
  gap: 15px;
}

//左边 右边 结构一样
.contetn_left,
.contetn_right {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  width: 420px;
  box-sizing: border-box;
  flex-shrink: 0;
  gap: 15px;
}

.contetn_center {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 15px;

  .map-container {
    flex: 1;
    min-height: 0;
    transition: all 0.3s ease;
    box-shadow: 0 0 15px rgba(0, 180, 220, 0.2);

    &:hover {
      box-shadow: 0 0 20px rgba(0, 220, 255, 0.3);
    }
  }

  .contetn_center-bottom {
    height: 300px;
    transition: all 0.3s ease;
    box-shadow: 0 0 15px rgba(0, 180, 220, 0.2);

    &:hover {
      box-shadow: 0 0 20px rgba(0, 220, 255, 0.3);
    }
  }
}

.contetn_lr-item {
  height: calc((100% - 30px) / 3);
  transition: all 0.3s ease;
  box-shadow: 0 0 15px rgba(0, 180, 220, 0.2);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 20px rgba(0, 220, 255, 0.3);
  }
}

@media (max-width: 1600px) {

  .contetn_left,
  .contetn_right {
    width: 380px;
  }

  .contetn_center {
    margin: 0 20px;
  }
}

@media (max-width: 1400px) {

  .contetn_left,
  .contetn_right {
    width: 360px;
  }

  .contetn_center {
    margin: 0 15px;
  }
}
</style>
