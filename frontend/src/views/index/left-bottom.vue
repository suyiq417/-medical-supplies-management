<script setup lang="ts">
import { useRouter } from 'vue-router';
import { inventoryAlerts } from "@/api/modules/index";
import SeamlessScroll from "@/components/seamless-scroll";
import { computed, onMounted, reactive, ref } from "vue";
import { useSettingStore } from "@/stores";
import { storeToRefs } from "pinia";
import EmptyCom from "@/components/empty-com";
import { ElMessage } from "element-plus";
import { Location, Clock, WarningFilled } from '@element-plus/icons-vue';
import type { InventoryAlert, MedicalSupply } from "@/types/models";

interface AlertListItem {
  id: number;
  hospitalName: string;
  district: string;
  address: string;
  supplyName: string;
  requestTime: string;
  requestContent: string;
  urgencyLevel: 'emergency' | 'urgent' | 'normal';
  alertType: string;
  alertTypeDisplay: string;
}

const router = useRouter();

const settingStore = useSettingStore();
const { defaultOption, indexConfig } = storeToRefs(settingStore);

const state = reactive<{
  data: { total_alerts: number; unresolved_alerts: number } | null;
  list: AlertListItem[];
  defaultOption: any;
  scroll: boolean;
  loading: boolean;
}>({
  data: null,
  list: [],
  defaultOption: {
    ...defaultOption.value,
    singleHeight: 256,
    limitScrollNum: 3,
  },
  scroll: true,
  loading: false
});

const getAlertTypeClass = (type: string) => {
  switch (type) {
    case 'LS': return 'type-warning';
    case 'EX': return 'type-info';
    case 'ED': return 'type-danger';
    case 'CP': return 'type-success';
    default: return '';
  }
};

const formatTime = (isoString: string) => {
  try {
    const date = new Date(isoString); // 修复：使用传入的 isoString 来创建 Date 对象
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
  } catch (e) {
    return isoString;
  }
};

const getData = async () => {
  state.loading = true;
  try {
    const res = await inventoryAlerts<{
      total_alerts: number;
      unresolved_alerts: number;
      recent_alerts: (InventoryAlert & { supply: MedicalSupply | null, hospital: { name: string, region: string, address: string } })[];
    }>();

    if (res) {
      state.data = {
        total_alerts: res.total_alerts,
        unresolved_alerts: res.unresolved_alerts
      };

      state.list = res.recent_alerts.map((alert): AlertListItem => ({
        id: alert.alert_id,
        hospitalName: alert.hospital?.name || '未知医院',
        district: alert.hospital?.region || '',
        address: alert.hospital?.address || '',
        supplyName: alert.supply?.name || '未知物资',
        requestTime: formatTime(alert.created_at), // 修复：调用修正后的 formatTime
        requestContent: alert.message,
        urgencyLevel:
          alert.alert_type === 'ED' ? 'emergency' :
            alert.alert_type === 'LS' ? 'urgent' : 'normal',
        alertType: alert.alert_type,
        alertTypeDisplay: alert.alert_type_display
      }));

      // 根据新的更紧凑的列表项高度估算 singleHeight
      state.defaultOption.singleHeight = 85;
      state.defaultOption.limitScrollNum = 3;
    }
  } catch (err) {
    console.error("获取预警数据失败:", err);
    ElMessage.error('获取预警数据失败');
    state.data = null;
    state.list = [];
  } finally {
    state.loading = false;
  }
};

const getUrgencyText = (level: string) => {
  return {
    emergency: '急需',
    urgent: '紧急',
    normal: '普通'
  }[level] || '普通';
};

const goToAlerts = () => {
  router.push('/management/alerts');
};

const comName = computed(() => {
  if (indexConfig.value.leftBottomSwiper && state.list.length > state.defaultOption.limitScrollNum && state.defaultOption.limitScrollNum > 0) {
    return SeamlessScroll;
  } else {
    return 'ul';
  }
});

onMounted(() => {
  getData();
  const timer = setInterval(getData, 60000);

  return () => {
    clearInterval(timer);
  };
});
</script>

<template>
  <div class="alert-container clickable-area" v-loading="state.loading" @click="goToAlerts">
    <div class="alert-summary" v-if="state.data">
      <div class="summary-item">
        <div class="summary-value">{{ state.data.total_alerts }}</div>
        <div class="summary-label">预警总数</div>
      </div>
      <div class="summary-item danger">
        <div class="summary-value">{{ state.data.unresolved_alerts }}</div>
        <div class="summary-label">未解决预警</div>
      </div>
    </div>

    <div class="list-wrap beautify-scroll-def"
      :class="{ 'overflow-y-auto': !indexConfig.leftBottomSwiper || state.list.length <= state.defaultOption.limitScrollNum }">
      <SeamlessScroll v-if="comName === SeamlessScroll" :list="state.list" v-model="state.scroll"
        :singleHeight="state.defaultOption.singleHeight" :step="state.defaultOption.step"
        :limitScrollNum="state.defaultOption.limitScrollNum" :hover="state.defaultOption.hover"
        :singleWaitTime="state.defaultOption.singleWaitTime" :wheel="state.defaultOption.wheel">
        <ul class="alert-list">
          <li class="alert-item" v-for="(item, i) in state.list" :key="item.id">
            <span class="order-num">{{ i + 1 }}</span>
            <div class="alert-content">
              <div class="row header-row">
                <span class="hospital-name">{{ item.hospitalName }}</span>
                <div class="tags">
                  <span class="alert-type" :class="getAlertTypeClass(item.alertType)">
                    {{ item.alertTypeDisplay }}
                  </span>
                  <span class="urgency-level" :class="{
                    'type-emergency': item.urgencyLevel === 'emergency',
                    'type-urgent': item.urgencyLevel === 'urgent',
                    'type-normal': item.urgencyLevel === 'normal'
                  }">{{ getUrgencyText(item.urgencyLevel) }}</span>
                </div>
              </div>
              <div class="row info-row supply-row">
                <el-icon>
                  <WarningFilled />
                </el-icon>
                <span class="label">物资:</span>
                <span class="value supply-name">{{ item.supplyName }}</span>
              </div>
              <div class="row info-row">
                <el-icon>
                  <Location />
                </el-icon>
                <span class="label">地址:</span>
                <span class="value address-value" :title="item.district + item.address">{{ item.district }}{{
                  item.address }}</span>
              </div>
              <div class="row info-row time-row">
                <el-icon>
                  <Clock />
                </el-icon>
                <span class="label">时间:</span>
                <span class="value time-value">{{ item.requestTime }}</span>
              </div>
              <div class="row message-row">
                <span class="label">内容:</span>
                <span class="value message-value" :title="item.requestContent">{{ item.requestContent }}</span>
              </div>
            </div>
          </li>
        </ul>
      </SeamlessScroll>
      <ul class="alert-list" v-else-if="comName === 'ul' && state.list.length > 0">
        <li class="alert-item" v-for="(item, i) in state.list" :key="item.id">
          <span class="order-num">{{ i + 1 }}</span>
          <div class="alert-content">
            <div class="row header-row">
              <span class="hospital-name">{{ item.hospitalName }}</span>
              <div class="tags">
                <span class="alert-type" :class="getAlertTypeClass(item.alertType)">
                  {{ item.alertTypeDisplay }}
                </span>
                <span class="urgency-level" :class="{
                  'type-emergency': item.urgencyLevel === 'emergency',
                  'type-urgent': item.urgencyLevel === 'urgent',
                  'type-normal': item.urgencyLevel === 'normal'
                }">{{ getUrgencyText(item.urgencyLevel) }}</span>
              </div>
            </div>
            <div class="row info-row supply-row">
              <el-icon>
                <WarningFilled />
              </el-icon>
              <span class="label">物资:</span>
              <span class="value supply-name">{{ item.supplyName }}</span>
            </div>
            <div class="row info-row">
              <el-icon>
                <Location />
              </el-icon>
              <span class="label">地址:</span>
              <span class="value address-value" :title="item.district + item.address">{{ item.district }}{{ item.address
              }}</span>
            </div>
            <div class="row info-row time-row">
              <el-icon>
                <Clock />
              </el-icon>
              <span class="label">时间:</span>
              <span class="value time-value">{{ item.requestTime }}</span>
            </div>
            <div class="row message-row">
              <span class="label">内容:</span>
              <span class="value message-value" :title="item.requestContent">{{ item.requestContent }}</span>
            </div>
          </div>
        </li>
      </ul>
      <el-empty v-if="!state.loading && state.list.length === 0" description="暂无预警信息" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.clickable-area {
  cursor: pointer;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: rgba(255, 255, 255, 0.05);
  }
}

.alert-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 10px;
  box-sizing: border-box;
}

.alert-summary {
  display: flex;
  justify-content: space-around;
  margin-bottom: 12px;
  pointer-events: none;

  .summary-item {
    text-align: center;

    &.danger .summary-value {
      color: #F56C6C;
    }

    .summary-value {
      font-size: 20px;
      font-weight: bold;
      color: #00fdfa;
      margin-bottom: 2px;
    }

    .summary-label {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.7);
    }
  }
}

.list-wrap {
  overflow: hidden;
  width: 100%;
  flex: 1;
  position: relative;
}

.overflow-y-auto {
  overflow-y: auto;
}

.alert-list {
  width: 100%;
  height: 100%;
  padding: 0;
  margin: 0;
  list-style: none;

  .alert-item {
    display: flex;
    align-items: flex-start;
    padding: 8px 6px;
    margin-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    font-size: 13px;
    color: rgba(255, 255, 255, 0.9);
    background-color: rgba(0, 50, 80, 0.1);
    border-radius: 4px;

    &:last-child {
      margin-bottom: 0;
      border-bottom: none;
    }

    .order-num {
      margin-right: 8px;
      font-weight: bold;
      color: $primary-color;
      min-width: 18px;
      text-align: center;
      line-height: 1.4;
      font-size: 14px;
    }

    .alert-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 5px;

      .row {
        display: flex;
        align-items: center;
        line-height: 1.4;
        gap: 4px;

        .el-icon {
          color: rgba(255, 255, 255, 0.6);
          font-size: 14px;
        }
      }

      .header-row {
        justify-content: space-between;
        margin-bottom: 2px;

        .hospital-name {
          font-weight: 600;
          color: #fff;
          font-size: 14px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: calc(100% - 100px);
        }

        .tags {
          display: flex;
          gap: 4px;
          flex-shrink: 0;
        }
      }

      .info-row {
        align-items: flex-start;

        .label {
          color: rgba(255, 255, 255, 0.6);
          flex-shrink: 0;
        }

        .value {
          color: rgba(255, 255, 255, 0.85);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          flex-grow: 1;
        }

        &.supply-row .value {
          font-weight: 600;
          color: #fff;
        }
      }

      .message-row {
        align-items: flex-start;

        .label {
          color: rgba(255, 255, 255, 0.6);
          flex-shrink: 0;
        }

        .message-value {
          color: rgba(255, 255, 255, 0.8);
          display: -webkit-box;
          -webkit-line-clamp: 1;
          -webkit-box-orient: vertical;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: normal;
          line-height: 1.4;
        }
      }

      .alert-type,
      .urgency-level {
        padding: 1px 5px;
        border-radius: 3px;
        font-size: 11px;
        font-weight: 500;
        flex-shrink: 0;
        white-space: nowrap;
      }

      .alert-type {
        &.type-warning {
          background: rgba(230, 162, 60, 0.2);
          color: #E6A23C;
        }

        &.type-info {
          background: rgba(144, 147, 153, 0.2);
          color: #909399;
        }

        &.type-danger {
          background: rgba(245, 108, 108, 0.2);
          color: #F56C6C;
        }

        &.type-success {
          background: rgba(103, 194, 58, 0.2);
          color: #67C23A;
        }
      }

      .urgency-level {
        &.type-emergency {
          color: #fc1a1a;
          background: rgba(252, 26, 26, 0.1);
          border: 1px solid rgba(252, 26, 26, 0.2);
        }

        &.type-urgent {
          color: #ff9800;
          background: rgba(255, 152, 0, 0.1);
          border: 1px solid rgba(255, 152, 0, 0.2);
        }

        &.type-normal {
          color: #29fc29;
          background: rgba(41, 252, 41, 0.1);
          border: 1px solid rgba(41, 252, 41, 0.2);
        }
      }
    }
  }
}

:deep(.el-empty__description p),
:deep(.el-empty__image) {
  color: rgba(255, 255, 255, 0.6);
}

:deep(.el-empty__image) {
  width: 80px;
}
</style>
