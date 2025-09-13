<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { requestFulfillment } from "@/api/modules/index";
import { ElMessage } from "element-plus";
import { useRouter } from 'vue-router';

const router = useRouter();

interface User {
  id: number;
  username: string;
  first_name?: string;
  last_name?: string;
}
interface RequestData {
  request_id: string;
  hospital_name: string;
  request_time: string;
  required_by: string;
  emergency: boolean;
  status: string;
  status_display: string;
  approval_time?: string | null;
  approver?: User | null;
  requester?: User | null;
}
interface FulfillmentData {
  pending_requests: RequestData[];
  approved_requests: RequestData[];
  fulfilled_requests: RequestData[];
}

const data = ref<FulfillmentData | null>(null);
const loading = ref(true);
let timer: number | null = null;

const pendingItemsRef = ref<HTMLElement | null>(null);
const approvedItemsRef = ref<HTMLElement | null>(null);
const fulfilledItemsRef = ref<HTMLElement | null>(null);

const isPendingHovering = ref(false);
const isApprovedHovering = ref(false);
const isFulfilledHovering = ref(false);

let scrollTimer: number | null = null;
const scrollSpeed = 1;
const scrollInterval = 50;

const scrollColumn = (element: HTMLElement | null, isHovering: boolean) => {
  if (!element || isHovering || element.scrollHeight <= element.clientHeight) {
    return;
  }

  if (element.scrollTop + element.clientHeight >= element.scrollHeight - 1) {
    element.scrollTop = 0;
  } else {
    element.scrollTop += scrollSpeed;
  }
};

const startAutoScroll = () => {
  stopAutoScroll();
  scrollTimer = setInterval(() => {
    scrollColumn(pendingItemsRef.value, isPendingHovering.value);
    scrollColumn(approvedItemsRef.value, isApprovedHovering.value);
    scrollColumn(fulfilledItemsRef.value, isFulfilledHovering.value);
  }, scrollInterval);
};

const stopAutoScroll = () => {
  if (scrollTimer) {
    clearInterval(scrollTimer);
    scrollTimer = null;
  }
};

const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return '未知';
  try {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }).replace(/\//g, '-');
  } catch (e) {
    console.error("Error formatting date:", dateString, e);
    return '日期无效';
  }
};

const getUserName = (user: User | null | undefined): string => {
  if (!user) return '未知';
  return user.username || '未知';
};

const getData = async () => {
  loading.value = true;
  try {
    const res: FulfillmentData = await requestFulfillment();
    if (res) {
      data.value = res;
      await nextTick();
      if (!scrollTimer) {
        startAutoScroll();
      }
    } else {
      data.value = null;
    }
  } catch (err: any) {
    console.error("获取请求履行数据失败:", err);
    data.value = null;
    ElMessage.error(`获取请求履行数据失败: ${err.message || '请检查网络连接或联系管理员'}`);
  } finally {
    loading.value = false;
  }
};

const viewRequestDetail = (requestId: string) => {
  if (!requestId) {
    console.error("Invalid request ID for navigation.");
    ElMessage.warning("无法导航：无效的请求 ID。");
    return;
  }
  router.push(`/management/requests/${requestId}`);
};

onMounted(async () => {
  await getData();
  await nextTick();
  startAutoScroll();
  timer = setInterval(getData, 60000);
});

onUnmounted(() => {
  stopAutoScroll();
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
});
</script>

<template>
  <div class="fulfillment-container" v-loading="loading">
    <template v-if="data">
      <div class="timelines">
        <div class="timeline-column">
          <div class="column-title">
            <div class="status-icon pending"></div>
            <span>待处理</span>
          </div>
          <div class="timeline-items" ref="pendingItemsRef" @mouseenter="isPendingHovering = true"
            @mouseleave="isPendingHovering = false">
            <div class="timeline-item" v-for="req in data.pending_requests" :key="req.request_id"
              @click="viewRequestDetail(req.request_id)" :title="`点击查看 ${req.hospital_name} 的请求详情`">
              <div class="item-header">
                <span class="hospital-name">{{ req.hospital_name }}</span>
                <span class="status pending" :class="{ 'is-emergency': req.emergency }">
                  {{ req.emergency ? '紧急' : req.status_display }}
                </span>
              </div>
              <div class="item-detail"><span class="label">申请人:</span> {{ getUserName(req.requester) }}</div>
              <div class="item-detail"><span class="label">申请时间:</span> {{ formatDate(req.request_time) }}</div>
              <div class="item-detail"><span class="label">需求时间:</span> {{ formatDate(req.required_by) }}</div>
            </div>
            <div class="empty-message" v-if="!data.pending_requests || data.pending_requests.length === 0">
              暂无待处理请求
            </div>
          </div>
        </div>

        <div class="timeline-column">
          <div class="column-title">
            <div class="status-icon approved"></div>
            <span>已批准</span>
          </div>
          <div class="timeline-items" ref="approvedItemsRef" @mouseenter="isApprovedHovering = true"
            @mouseleave="isApprovedHovering = false">
            <div class="timeline-item" v-for="req in data.approved_requests" :key="req.request_id"
              @click="viewRequestDetail(req.request_id)" :title="`点击查看 ${req.hospital_name} 的请求详情`">
              <div class="item-header">
                <span class="hospital-name">{{ req.hospital_name }}</span>
                <span class="status approved">{{ req.status_display }}</span>
              </div>
              <div class="item-detail"><span class="label">申请人:</span> {{ getUserName(req.requester) }}</div>
              <div class="item-detail"><span class="label">批准人:</span> {{ getUserName(req.approver) }}</div>
              <div class="item-detail"><span class="label">批准时间:</span> {{ formatDate(req.approval_time) }}</div>
              <div class="item-detail"><span class="label">需求时间:</span> {{ formatDate(req.required_by) }}</div>
            </div>
            <div class="empty-message" v-if="!data.approved_requests || data.approved_requests.length === 0">
              暂无已批准请求
            </div>
          </div>
        </div>

        <div class="timeline-column">
          <div class="column-title">
            <div class="status-icon fulfilled"></div>
            <span>已完成</span>
          </div>
          <div class="timeline-items" ref="fulfilledItemsRef" @mouseenter="isFulfilledHovering = true"
            @mouseleave="isFulfilledHovering = false">
            <div class="timeline-item" v-for="req in data.fulfilled_requests" :key="req.request_id"
              @click="viewRequestDetail(req.request_id)" :title="`点击查看 ${req.hospital_name} 的请求详情`">
              <div class="item-header">
                <span class="hospital-name">{{ req.hospital_name }}</span>
                <span class="status fulfilled">{{ req.status_display }}</span>
              </div>
              <div class="item-detail"><span class="label">申请人:</span> {{ getUserName(req.requester) }}</div>
              <div class="item-detail"><span class="label">批准人:</span> {{ getUserName(req.approver) }}</div>
              <div class="item-detail"><span class="label">批准时间:</span> {{ formatDate(req.approval_time) }}</div>
              <div class="item-detail"><span class="label">需求时间:</span> {{ formatDate(req.required_by) }}</div>
            </div>
            <div class="empty-message" v-if="!data.fulfilled_requests || data.fulfilled_requests.length === 0">
              暂无已完成请求
            </div>
          </div>
        </div>
      </div>
    </template>
    <div v-else-if="!loading" class="empty-data-message">
      无法加载请求履行数据或暂无数据。
    </div>
  </div>
</template>

<style scoped lang="scss">
.fulfillment-container {
  height: 100%;
  width: 100%;
  display: flex;
  box-sizing: border-box;

  .timelines {
    display: flex;
    flex-grow: 1;
    height: 100%;
    gap: 15px;
    padding: 5px 10px 10px 10px;
    box-sizing: border-box;
  }

  .timeline-column {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    background: rgba(0, 0, 0, 0.25);
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    overflow: hidden;

    .column-title {
      padding: 10px 12px;
      display: flex;
      align-items: center;
      gap: 8px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.15);
      font-weight: bold;
      color: #ffffff;
      background-color: rgba(0, 0, 0, 0.2);
      flex-shrink: 0;

      .status-icon {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        flex-shrink: 0;

        &.pending {
          background: #E6A23C;
        }

        &.approved {
          background: #409EFF;
        }

        &.fulfilled {
          background: #67C23A;
        }
      }

      span {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }

    .timeline-items {
      flex-grow: 1;
      overflow-y: auto;
      padding: 10px 12px;
      scroll-behavior: smooth;

      &::-webkit-scrollbar {
        width: 6px;
      }

      &::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.1);
        border-radius: 3px;
      }

      &::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 3px;
      }

      &::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.5);
      }

      .timeline-item {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 5px;
        padding: 10px 12px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: background-color 0.2s ease, border-color 0.2s ease;

        &:hover {
          background: rgba(255, 255, 255, 0.12);
          border-color: rgba(0, 253, 250, 0.6);
        }

        .item-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;

          .hospital-name {
            font-weight: bold;
            color: #00fdfa;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            flex-grow: 1;
            margin-right: 10px;
          }

          .status {
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 12px;
            flex-shrink: 0;
            font-weight: 500;
            white-space: nowrap;

            &.pending {
              background: rgba(230, 162, 60, 0.2);
              color: #E6A23C;
            }

            &.is-emergency {
              background: rgba(245, 108, 108, 0.2);
              color: #F56C6C;
              font-weight: bold;
            }

            &.approved {
              background: rgba(64, 158, 255, 0.2);
              color: #409EFF;
            }

            &.fulfilled {
              background: rgba(103, 194, 58, 0.2);
              color: #67C23A;
            }
          }
        }

        .item-detail {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.8);
          margin-top: 5px;
          line-height: 1.5;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;

          .label {
            color: rgba(255, 255, 255, 0.6);
            margin-right: 5px;
          }
        }
      }

      .empty-message {
        text-align: center;
        padding: 30px 15px;
        color: rgba(255, 255, 255, 0.6);
        font-style: italic;
        font-size: 13px;
      }
    }
  }

  .empty-data-message {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    width: 100%;
    color: rgba(255, 255, 255, 0.6);
    font-style: italic;
    font-size: 14px;
  }
}
</style>