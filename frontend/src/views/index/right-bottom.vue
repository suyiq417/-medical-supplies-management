<script setup lang="ts">
import { requestStatus } from "@/api/modules/index";
import SeamlessScroll from "@/components/seamless-scroll";
import { computed, onMounted, reactive, ref, onUnmounted } from "vue";
import { useSettingStore } from "@/stores";
import { storeToRefs } from "pinia";
import EmptyCom from "@/components/empty-com";
import { ElMessage } from "element-plus";
import { useRouter } from 'vue-router';
import type { RequestsOverview } from "@/types/models";

const router = useRouter();
const settingStore = useSettingStore();
const { defaultOption, indexConfig } = storeToRefs(settingStore);

interface StatusItem {
  id: string;
  status: string;
  status_display: string;
  count: number;
  percent: string;
}

const state = reactive<{
  data: RequestsOverview | null;
  list: StatusItem[];
  defaultOption: any;
  scroll: boolean;
  loading: boolean;
}>({
  data: null,
  list: [],
  defaultOption: {
    ...defaultOption.value,
    singleHeight: 252,
    limitScrollNum: 3,
    step: 0.5,
  },
  scroll: true,
  loading: false
});

// 获取数据
const getData = async () => {
  state.loading = true;
  try {
    const res: RequestsOverview = await requestStatus();
    if (res && res.by_status) {
      state.data = res;

      state.list = res.by_status.map((status, index) => ({
        id: `status-${index}`,
        status: status.status,
        status_display: status.status_display,
        count: status.count,
        percent: res.total_requests > 0 ? (status.count / res.total_requests * 100).toFixed(1) : '0.0'
      }));
    } else {
      state.data = null;
      state.list = [];
    }
  } catch (err) {
    console.error("获取请求状态数据失败:", err);
    ElMessage.error('获取请求状态数据失败');
    state.data = null;
    state.list = [];
  } finally {
    state.loading = false;
  }
};

// 获取状态标签的样式类
const getStatusClass = (status: string): string => {
  switch (status) {
    case 'DR': return 'status-draft';
    case 'SU': return 'status-submitted';
    case 'AP': return 'status-approved';
    case 'RJ': return 'status-rejected';
    case 'FU': return 'status-fulfilled';
    case 'CA': return 'status-cancelled';
    default: return '';
  }
};

// 跳转到请求列表页面
const goToRequests = () => {
  router.push('/management/requests');
};

// 获取组件名称
const comName = computed(() => {
  if (state.list.length === 0) {
    return EmptyCom;
  }
  return indexConfig.value.rightBottomSwiper ? SeamlessScroll : 'div';
});

// 计算滚动配置
const scrollOption = computed(() => {
  return {
    ...state.defaultOption,
    limitScrollNum: Math.min(state.defaultOption.limitScrollNum, state.list.length > 0 ? state.list.length : 1),
  };
});

let timer: number | null = null;

onMounted(() => {
  getData();
  timer = setInterval(getData, 60000);
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
});
</script>

<template>
  <div class="request-status-container" v-loading="state.loading" @click="goToRequests" style="cursor: pointer;">
    <div class="status-summary" v-if="state.data">
      <div class="summary-item">
        <div class="summary-value">{{ state.data.total_requests ?? 0 }}</div>
        <div class="summary-label">请求总数</div>
      </div>
      <div class="summary-item emergency">
        <div class="summary-value">{{ state.data.emergency_requests ?? 0 }}</div>
        <div class="summary-label">紧急请求</div>
      </div>
      <div class="summary-item pending">
        <div class="summary-value">{{ state.data.pending_approval ?? 0 }}</div>
        <div class="summary-label">待审批</div>
      </div>
    </div>
    <div v-else class="status-summary-placeholder">
      <div class="summary-item">
        <div class="summary-value">-</div>
        <div class="summary-label">请求总数</div>
      </div>
      <div class="summary-item emergency">
        <div class="summary-value">-</div>
        <div class="summary-label">紧急请求</div>
      </div>
      <div class="summary-item pending">
        <div class="summary-value">-</div>
        <div class="summary-label">待审批</div>
      </div>
    </div>

    <div class="right_bottom_wrap beautify-scroll-def" :class="{ 'overflow-y-auto': comName === 'div' }">
      <component :is="comName" :list="state.list" v-model="state.scroll" :option="scrollOption"
        v-if="comName === SeamlessScroll">
        <div class="status-list">
          <div class="status-item" v-for="item in state.list" :key="item.id">
            <div class="status-header">
              <div class="status-tag" :class="getStatusClass(item.status)">{{ item.status_display }}</div>
              <div class="status-count">{{ item.count }} 个请求</div>
            </div>
            <div class="status-bar-container">
              <el-tooltip :content="`${item.percent}%`" placement="top">
                <div class="status-bar">
                  <div class="status-fill" :class="getStatusClass(item.status)" :style="{ width: `${item.percent}%` }">
                  </div>
                </div>
              </el-tooltip>
              <div class="status-percent">{{ item.percent }}%</div>
            </div>
          </div>
        </div>
      </component>
      <div class="status-list" v-else-if="comName === 'div'">
        <div class="status-item" v-for="item in state.list" :key="item.id">
          <div class="status-header">
            <div class="status-tag" :class="getStatusClass(item.status)">{{ item.status_display }}</div>
            <div class="status-count">{{ item.count }} 个请求</div>
          </div>
          <div class="status-bar-container">
            <el-tooltip :content="`${item.percent}%`" placement="top">
              <div class="status-bar">
                <div class="status-fill" :class="getStatusClass(item.status)" :style="{ width: `${item.percent}%` }">
                </div>
              </div>
            </el-tooltip>
            <div class="status-percent">{{ item.percent }}%</div>
          </div>
        </div>
      </div>
      <EmptyCom v-else />
    </div>
  </div>
</template>

<style scoped lang="scss">
.request-status-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 10px;
  box-sizing: border-box;
}

.status-summary,
.status-summary-placeholder {
  display: flex;
  justify-content: space-around;
  margin-bottom: 10px;
  padding: 5px 0;
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 4px;

  .summary-item {
    text-align: center;
    flex: 1;

    &.emergency .summary-value {
      color: #F56C6C;
    }

    &.pending .summary-value {
      color: #E6A23C;
    }

    .summary-value {
      font-size: 20px;
      font-weight: bold;
      color: #00fdfa;
      margin-bottom: 2px;
      line-height: 1.1;
    }

    .summary-label {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.75);
    }
  }
}

.status-summary-placeholder {
  .summary-value {
    color: rgba(255, 255, 255, 0.5);
  }
}

.right_bottom_wrap {
  overflow: hidden;
  width: 100%;
  flex: 1;
}

.overflow-y-auto {
  overflow-y: auto;
}

.status-list {
  padding: 5px 0;

  .status-item {
    margin-bottom: 18px;
    padding: 10px;
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 4px;

    &:last-child {
      margin-bottom: 0;
    }

    .status-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;

      .status-tag {
        padding: 3px 8px;
        border-radius: 3px;
        font-size: 12px;
        font-weight: 500;

        &.status-draft {
          background: rgba(144, 147, 153, 0.2);
          color: #909399;
          border: 1px solid rgba(144, 147, 153, 0.3);
        }

        &.status-submitted {
          background: rgba(64, 158, 255, 0.15);
          color: #409EFF;
          border: 1px solid rgba(64, 158, 255, 0.3);
        }

        &.status-approved {
          background: rgba(103, 194, 58, 0.15);
          color: #67C23A;
          border: 1px solid rgba(103, 194, 58, 0.3);
        }

        &.status-rejected {
          background: rgba(245, 108, 108, 0.15);
          color: #F56C6C;
          border: 1px solid rgba(245, 108, 108, 0.3);
        }

        &.status-fulfilled {
          background: rgba(0, 253, 250, 0.15);
          color: #00fdfa;
          border: 1px solid rgba(0, 253, 250, 0.3);
        }

        &.status-cancelled {
          background: rgba(230, 162, 60, 0.15);
          color: #E6A23C;
          border: 1px solid rgba(230, 162, 60, 0.3);
        }
      }

      .status-count {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.8);
      }
    }

    .status-bar-container {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .status-bar {
      flex-grow: 1;
      height: 10px;
      background: rgba(255, 255, 255, 0.15);
      border-radius: 5px;
      overflow: hidden;
      cursor: pointer;

      .status-fill {
        height: 100%;
        border-radius: 5px;
        transition: width 0.3s ease;

        &.status-draft {
          background: #909399;
        }

        &.status-submitted {
          background: #409EFF;
        }

        &.status-approved {
          background: #67C23A;
        }

        &.status-rejected {
          background: #F56C6C;
        }

        &.status-fulfilled {
          background: #00fdfa;
        }

        &.status-cancelled {
          background: #E6A23C;
        }
      }
    }

    .status-percent {
      font-size: 13px;
      color: rgba(255, 255, 255, 0.8);
      min-width: 40px;
      text-align: right;
    }
  }
}

.beautify-scroll-def {
  &::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background-color: rgba(0, 253, 250, 0.3);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-track {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
  }
}
</style>
