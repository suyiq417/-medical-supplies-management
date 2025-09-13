<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue';
import { onUnmounted } from 'vue';
import { getHospitalDetail, getHospitalAlerts, getHospitalInventory, getHospitalRequests } from '@/api/modules/index';
import * as echarts from 'echarts';
import { ElSkeleton, ElEmpty, ElTag, ElProgress, ElTooltip, ElButton } from 'element-plus';
import { Calendar as CalendarIcon, TrendCharts, Warning, Box, SetUp, Van, InfoFilled, WarningFilled, DocumentCopy, CollectionTag, LocationInformation, Place, Phone, Message, Link, User } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';

const props = defineProps<{
  hospitalId: string;
  hospitalName: string;
}>();

const router = useRouter();

// 数据状态
const loading = ref(true);
const hospitalData = ref<any>(null);
const alertsData = ref<any[]>([]);
const inventoryData = ref<any[]>([]);
const requestsData = ref<any[]>([]);
const supplyCategoryCounts = ref<{ category: string, count: number }[]>([]);

// 图表实例
const storageChartRef = ref<HTMLElement | null>(null);
let storageChart: echarts.ECharts | null = null;

// 库存使用率计算
const usageRatio = computed((): string => {
  if (!hospitalData.value) return '0';
  return hospitalData.value.current_capacity && hospitalData.value.storage_volume
    ? (hospitalData.value.current_capacity / hospitalData.value.storage_volume * 100).toFixed(1)
    : '0';
});

// 使用率状态
const usageStatus = computed((): 'success' | 'warning' | 'danger' => {
  const ratio = parseFloat(usageRatio.value);
  if (ratio >= 90) return 'danger';
  if (ratio >= 70) return 'warning';
  return 'success';
});

// 获取预警优先级文本
const getAlertPriorityText = (level: number): string => {
  if (level >= 3) return '高';
  if (level >= 2) return '中';
  return '低';
};

// 获取请求优先级文本和样式
const getRequestPriorityInfo = (level: number): { text: string, type: 'danger' | 'warning' | 'info' } => {
  if (level >= 4) return { text: '紧急', type: 'danger' };
  if (level >= 3) return { text: '高', type: 'warning' };
  return { text: '普通', type: 'info' };
};

// 初始化图表
const initStorageChart = () => {
  if (!storageChartRef.value || !hospitalData.value) return;

  if (storageChart) {
    storageChart.dispose();
    storageChart = null;
  }

  storageChart = echarts.init(storageChartRef.value);

  const currentUsageRatio = parseFloat(usageRatio.value);

  const option = {
    series: [
      {
        type: 'gauge',
        startAngle: 90,
        endAngle: -270,
        pointer: { show: false },
        progress: {
          show: true,
          overlap: false,
          roundCap: true,
          clip: false,
          itemStyle: {
            color: currentUsageRatio >= 90 ? '#f56c6c' : (currentUsageRatio >= 70 ? '#e6a23c' : {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [{ offset: 0, color: '#07c2ff' }, { offset: 1, color: '#0068ff' }]
            })
          }
        },
        axisLine: {
          lineStyle: {
            width: 10,
            color: [
              [currentUsageRatio / 100, 'rgba(10, 120, 200, 0.8)'],
              [1, 'rgba(10, 40, 80, 0.2)']
            ]
          }
        },
        splitLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false },
        title: {
          fontSize: 14,
          offsetCenter: [0, '30%'],
          color: '#00ccff'
        },
        detail: {
          width: 50,
          height: 14,
          fontSize: 18,
          color: '#fff',
          formatter: currentUsageRatio.toFixed(1) + '%',
          offsetCenter: [0, 0]
        },
        data: [{ value: currentUsageRatio }]
      }
    ]
  };

  storageChart.setOption(option);
};

// 获取医院详情数据
const fetchHospitalDetail = async () => {
  loading.value = true;
  hospitalData.value = null;
  alertsData.value = [];
  inventoryData.value = [];
  requestsData.value = [];
  supplyCategoryCounts.value = [];

  try {
    if (!props.hospitalId) {
      loading.value = false;
      return;
    }

    const [detail, alertsResponse, inventoryResponse, requestsResponse] = await Promise.all([
      getHospitalDetail(props.hospitalId),
      getHospitalAlerts(props.hospitalId),
      getHospitalInventory(props.hospitalId),
      getHospitalRequests(props.hospitalId)
    ]);

    hospitalData.value = detail;

    alertsData.value = (alertsResponse?.results && Array.isArray(alertsResponse.results))
      ? alertsResponse.results.slice(0, 3)
      : [];

    inventoryData.value = (inventoryResponse?.results && Array.isArray(inventoryResponse.results))
      ? inventoryResponse.results
      : [];

    requestsData.value = (requestsResponse?.results && Array.isArray(requestsResponse.results))
      ? requestsResponse.results.slice(0, 3)
      : [];

    if (inventoryData.value && inventoryData.value.length > 0) {
      const categoryMap = new Map<string, number>();
      inventoryData.value.forEach(item => {
        const category = item?.supply?.category_display || '未分类';
        categoryMap.set(category, (categoryMap.get(category) || 0) + 1);
      });
      supplyCategoryCounts.value = Array.from(categoryMap.entries()).map(([category, count]) => ({ category, count }));
    } else {
      supplyCategoryCounts.value = [];
    }

    await nextTick();
    initStorageChart();

  } catch (error) {
    console.error('获取医院详情失败:', error);
  } finally {
    loading.value = false;
  }
};

// 根据医院等级获取显示文本和颜色
const getLevelInfo = (level: number) => {
  const levelMap: { [key: number]: { text: string, color: string } } = {
    1: { text: '社区医院', color: '#909399' },
    2: { text: '区级医院', color: '#67c23a' },
    3: { text: '三甲医院', color: '#409eff' },
    4: { text: '三乙医院', color: '#67c23a' },
    5: { text: '二甲医院', color: '#e6a23c' },
    6: { text: '二乙医院', color: '#f56c6c' },
    7: { text: '一甲医院', color: '#f56c6c' },
    8: { text: '一乙医院', color: '#f56c6c' },
    9: { text: '其他', color: '#909399' }
  };
  return levelMap[level] || { text: '未知', color: '#909399' };
};

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  try {
    return date.toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', hour12: false
    }).replace(/\//g, '-');
  } catch (e) {
    console.error("日期格式化错误:", e);
    return dateString;
  }
};

// 获取请求状态对应的标签类型
const getRequestStatusType = (status: string): 'success' | 'warning' | 'info' | 'danger' | 'primary' => {
  const statusMap: { [key: string]: 'success' | 'warning' | 'info' | 'danger' | 'primary' } = {
    'DR': 'info',
    'SU': 'warning',
    'AP': 'success',
    'RJ': 'danger',
    'FU': 'success',
    'CA': 'info'
  };
  return statusMap[status] || 'info';
};

// 获取预警类型对应的标签类型
const getAlertType = (type: string): { text: string, type: 'success' | 'warning' | 'info' | 'danger' | 'primary' } => {
  const typeMap: { [key: string]: { text: string, type: 'success' | 'warning' | 'info' | 'danger' | 'primary' } } = {
    'LS': { text: '库存不足', type: 'danger' },
    'EX': { text: '即将过期', type: 'warning' },
    'ED': { text: '已过期', type: 'danger' },
    'CP': { text: '容量预警', type: 'warning' }
  };
  return typeMap[type] || { text: '未知', type: 'info' };
};

// 获取预警等级对应的颜色类
const getAlertLevelClass = (level: number): string => {
  if (level >= 3) return 'high-level';
  if (level >= 2) return 'medium-level';
  return 'low-level';
};

// 跳转到医院详情页
const goToHospitalDetail = () => {
  if (props.hospitalId) {
    router.push(`/management/hospitals/${props.hospitalId}`);
  }
};

// 窗口大小变化时调整图表尺寸
const handleResize = () => {
  if (storageChart) {
    storageChart.resize();
  }
};

// 监听医院ID变化
watch(() => props.hospitalId, (newId) => {
  if (newId) {
    fetchHospitalDetail();
  } else {
    hospitalData.value = null;
    alertsData.value = [];
    inventoryData.value = [];
    requestsData.value = [];
    supplyCategoryCounts.value = [];
    loading.value = false;
    if (storageChart) {
      storageChart.dispose();
      storageChart = null;
    }
  }
}, { immediate: true });

onMounted(() => {
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (storageChart) {
    storageChart.dispose();
    storageChart = null;
  }
});
</script>

<template>
  <div class="hospital-detail" @click="goToHospitalDetail" style="cursor: pointer;">
    <!-- 无选中医院提示 -->
    <div v-if="!hospitalId" class="empty-container">
      <el-empty description="请从地图选择一个医院" :image-size="80">
        <div class="empty-text">点击地图上的医院点位获取详细信息</div>
      </el-empty>
    </div>

    <!-- 加载中状态 -->
    <el-skeleton :loading="loading" animated v-else>
      <template #template>
        <div style="padding: 15px;">
          <el-skeleton-item variant="text" style="width: 80%" />
          <div style="display: flex; justify-content: space-between; margin-top: 15px;">
            <el-skeleton-item variant="text" style="width: 30%" />
            <el-skeleton-item variant="text" style="width: 30%" />
          </div>
          <el-skeleton-item variant="h3" style="width: 100%; margin-top: 10px;" />
          <el-skeleton-item variant="text" style="width: 100%; margin-top: 10px;" />
          <el-skeleton-item variant="text" style="width: 90%; margin-top: 5px;" />
          <el-skeleton-item variant="text" style="width: 80%; margin-top: 5px;" />
        </div>
      </template>

      <!-- 实际内容 -->
      <template #default>
        <!-- 医院基本信息 - 增强版头部 -->
        <div class="detail-header">
          <div class="header-main">
            <div class="hospital-name">{{ hospitalName }}</div>
            <div class="hospital-info">
              <el-tag v-if="hospitalData?.level" :color="getLevelInfo(hospitalData.level).color" effect="dark"
                size="small">
                {{ getLevelInfo(hospitalData.level).text }}
              </el-tag>
              <el-tag v-if="hospitalData?.region" type="info" effect="plain" size="small">
                {{ hospitalData.region }}
              </el-tag>
              <el-tag :type="usageStatus" effect="plain" size="small">
                使用率: {{ usageRatio }}%
              </el-tag>
              <el-tag v-if="alertsData.length > 0" type="danger" effect="dark" size="small">
                {{ alertsData.length }}个预警
              </el-tag>
            </div>
          </div>
          <div class="quick-stats">
            <div class="stat-item">
              <div class="stat-value">{{ hospitalData?.current_capacity || 0 }}/{{ hospitalData?.storage_volume || 0 }}
              </div>
              <div class="stat-label">容量 (m³)</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ inventoryData.length || 0 }}</div>
              <div class="stat-label">物资批次</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ requestsData.length || 0 }}</div>
              <div class="stat-label">近期请求</div>
            </div>
          </div>
        </div>

        <!-- 库存使用情况 - 增强视觉效果 -->
        <div class="detail-section">
          <div class="section-title with-tooltip">
            <TrendCharts class="icon" />
            <span>库存使用情况</span>
            <el-tooltip content="显示当前库存使用情况和容量数据" placement="top">
              <InfoFilled class="info-icon" />
            </el-tooltip>
          </div>
          <div class="storage-info-grid">
            <div class="usage-chart">
              <div ref="storageChartRef" class="gauge-chart"></div>
            </div>
            <div class="storage-stats">
              <div class="stat-row">
                <div class="stat-icon total-icon">
                  <Box class="icon-in-circle" />
                </div>
                <div class="stat-content">
                  <div class="stat-label">总容量</div>
                  <div class="stat-value">{{ hospitalData?.storage_volume || 0 }} m³</div>
                </div>
              </div>
              <div class="stat-row">
                <div class="stat-icon used-icon">
                  <DocumentCopy class="icon-in-circle" />
                </div>
                <div class="stat-content">
                  <div class="stat-label">已用容量</div>
                  <div class="stat-value">{{ hospitalData?.current_capacity || 0 }} m³</div>
                </div>
              </div>
              <div class="stat-row">
                <div class="stat-icon threshold-icon">
                  <WarningFilled class="icon-in-circle" />
                </div>
                <div class="stat-content">
                  <div class="stat-label">预警阈值</div>
                  <div class="stat-value">{{ hospitalData?.warning_threshold || 0 }}%</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 物资分类统计 -->
          <div class="category-stats" v-if="supplyCategoryCounts.length > 0">
            <div class="category-title">
              <CollectionTag class="category-icon" />
              物资分类统计 (按批次)
            </div>
            <div class="category-grid">
              <div v-for="(item, index) in supplyCategoryCounts" :key="index" class="category-item">
                <el-tooltip :content="item.category" placement="top">
                  <div class="category-name">{{ item.category }}</div>
                </el-tooltip>
                <div class="category-count">{{ item.count }}</div>
              </div>
            </div>
          </div>
          <div class="empty-content" v-else-if="!loading && inventoryData.length === 0">
            <el-empty description="暂无库存信息" :image-size="60"></el-empty>
          </div>
        </div>

        <!-- 医院地址和联系方式 - 优化显示 -->
        <div class="detail-section">
          <div class="section-title">
            <SetUp class="icon" />
            <span>基本信息</span>
          </div>
          <div class="info-content">
            <div class="info-row">
              <span class="label"><el-icon>
                  <InfoFilled />
                </el-icon> 机构编码:</span>
              <span class="value code">{{ hospitalData?.org_code || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="label"><el-icon>
                  <LocationInformation />
                </el-icon> 所在地区:</span>
              <span class="value">{{ hospitalData?.region || '-' }}</span>
            </div>
            <div class="info-row full-width">
              <span class="label"><el-icon>
                  <Place />
                </el-icon> 详细地址:</span>
              <span class="value address">{{ hospitalData?.address || '-' }}</span>
            </div>
            <div class="info-row" v-if="hospitalData?.contact_info?.phone">
              <span class="label"><el-icon>
                  <Phone />
                </el-icon> 联系电话:</span>
              <span class="value phone">{{ hospitalData.contact_info.phone }}</span>
            </div>
            <div class="info-row" v-if="hospitalData?.contact_info?.email">
              <span class="label"><el-icon>
                  <Message />
                </el-icon> 电子邮箱:</span>
              <span class="value email">{{ hospitalData.contact_info.email }}</span>
            </div>
            <div class="info-row" v-if="hospitalData?.contact_info?.website">
              <span class="label"><el-icon>
                  <Link />
                </el-icon> 官方网站:</span>
              <span class="value website"><a :href="hospitalData.contact_info.website" target="_blank"
                  rel="noopener noreferrer">{{ hospitalData.contact_info.website }}</a></span>
            </div>
          </div>
        </div>

        <!-- 预警信息 - 增强显示 -->
        <div class="detail-section alerts-section" v-if="alertsData.length > 0">
          <div class="section-title">
            <Warning class="icon" />
            <span>当前预警 ({{ alertsData.length }})</span>
          </div>

          <div class="alerts-container enhanced">
            <div v-for="(alert, index) in alertsData" :key="index" class="alert-item"
              :class="getAlertLevelClass(alert.priority || 1)">
              <div class="alert-header">
                <div>
                  <el-tag :type="getAlertType(alert.alert_type).type" size="small" effect="dark">
                    {{ getAlertType(alert.alert_type).text }}
                  </el-tag>
                  <el-tag v-if="alert.priority"
                    :type="alert.priority >= 3 ? 'danger' : (alert.priority >= 2 ? 'warning' : 'info')" size="small"
                    effect="light" style="margin-left: 5px;">
                    优先级: {{ getAlertPriorityText(alert.priority) }}
                  </el-tag>
                </div>
                <span class="alert-time">{{ formatDate(alert.created_at) }}</span>
              </div>
              <div class="alert-message">{{ alert.message }}</div>
              <div class="alert-context" v-if="alert.supply || alert.batch">
                <span v-if="alert.supply">物资: {{ alert.supply.name }}</span>
                <span v-if="alert.batch" style="margin-left: 10px;">批号: {{ alert.batch.batch_number }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="detail-section" v-else-if="!loading">
          <div class="section-title">
            <Warning class="icon" />
            <span>当前预警</span>
          </div>
          <div class="empty-content">
            <el-empty description="暂无预警信息" :image-size="60"></el-empty>
          </div>
        </div>

        <!-- 最近请求记录 - 增强显示 -->
        <div class="detail-section">
          <div class="section-title">
            <Van class="icon" />
            <span>最近物资请求</span>
          </div>

          <div class="requests-container enhanced" v-if="requestsData.length > 0">
            <div class="request-item" v-for="(request, index) in requestsData" :key="index">
              <div class="request-header">
                <div class="id-container">
                  <span class="request-label">申请单:</span>
                  <el-tooltip :content="request.request_id" placement="top">
                    <span class="request-id">{{ request.request_id.substring(0, 8) }}...</span>
                  </el-tooltip>
                </div>
                <div>
                  <el-tag v-if="request.priority" :type="getRequestPriorityInfo(request.priority).type" size="small"
                    effect="light" style="margin-right: 5px;">
                    {{ getRequestPriorityInfo(request.priority).text }}
                  </el-tag>
                  <el-tag :type="getRequestStatusType(request.status)" size="small" effect="dark">
                    {{ request.status_display }}
                  </el-tag>
                </div>
              </div>
              <div class="request-details">
                <div class="detail-item">
                  <CalendarIcon class="icon-small" />
                  <span>申请: {{ formatDate(request.request_time) }}</span>
                </div>
                <div class="detail-item" v-if="request.required_by">
                  <CalendarIcon class="icon-small" />
                  <span>需求: {{ formatDate(request.required_by) }}</span>
                </div>
                <div class="detail-item" v-if="request.requester">
                  <User class="icon-small" />
                  <span>申请人: {{ request.requester?.username || '未知' }}</span>
                </div>
                <div class="detail-item" v-if="request.emergency">
                  <el-tag type="danger" size="small" effect="dark">紧急</el-tag>
                </div>
              </div>
              <div class="request-summary" v-if="request.items && request.items.length">
                <div class="summary-label">申请物资 ({{ request.items.length }}项):</div>
                <div class="summary-items">
                  <el-tooltip v-for="(item, idx) in request.items.slice(0, 3)" :key="idx"
                    :content="`${item.supply?.name || '未知物资'} x ${item.quantity} ${item.supply?.unit || ''}`"
                    placement="top">
                    <el-tag size="small" effect="plain">
                      {{ item.supply?.name ? (item.supply.name.length > 6 ? item.supply.name.substring(0, 5) + '...' :
                        item.supply.name) : '未知' }} x {{ item.quantity }}
                    </el-tag>
                  </el-tooltip>
                  <span v-if="request.items.length > 3" class="more-items">
                    +{{ request.items.length - 3 }}项
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div class="empty-content" v-else-if="!loading">
            <el-empty description="暂无请求记录" :image-size="60"></el-empty>
          </div>
        </div>
      </template>
    </el-skeleton>
  </div>
</template>

<style scoped lang="scss">
.hospital-detail {
  height: 100%;
  overflow-y: auto;
  color: #eee;
  padding: 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 180, 220, 0.5) rgba(0, 30, 60, 0.2);
  transition: background-color 0.2s ease;

  &:hover {
    background-color: rgba(255, 255, 255, 0.03);
  }

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(0, 30, 60, 0.2);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background-color: rgba(0, 180, 220, 0.5);
    border-radius: 3px;
  }

  .empty-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    cursor: default;

    .empty-text {
      color: rgba(255, 255, 255, 0.5);
      font-size: 12px;
      margin-top: 10px;
    }
  }

  .detail-header {
    padding: 15px 15px 10px;
    background: linear-gradient(to right, rgba(0, 30, 60, 0.4), rgba(0, 60, 120, 0.2));
    border-radius: 4px;
    margin: 10px;
    box-shadow: 0 1px 4px rgba(0, 200, 255, 0.1);

    .header-main {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .hospital-name {
      font-size: 20px;
      font-weight: bold;
      color: #00eaff;
      text-shadow: 0 0 10px rgba(0, 234, 255, 0.3);
    }

    .hospital-info {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;

      .el-tag {
        margin-right: 5px;
        margin-bottom: 5px;

        &.el-tag--dark {
          color: #fff;
        }
      }
    }

    .quick-stats {
      display: flex;
      margin-top: 15px;
      border-top: 1px solid rgba(0, 180, 220, 0.2);
      padding-top: 12px;

      .stat-item {
        flex: 1;
        text-align: center;

        .stat-value {
          font-size: 16px;
          font-weight: bold;
          color: #fff;
        }

        .stat-label {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.6);
          margin-top: 3px;
        }
      }
    }
  }

  .detail-section {
    margin: 12px 10px;
    padding: 12px 15px;
    border-radius: 4px;
    background: rgba(0, 20, 40, 0.3);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    border-left: 3px solid rgba(0, 150, 200, 0.5);

    &.alerts-section {
      border-left-color: rgba(255, 70, 70, 0.7);
    }

    .section-title {
      display: flex;
      align-items: center;
      font-size: 15px;
      font-weight: bold;
      margin-bottom: 15px;
      color: #00ccff;

      &.with-tooltip {
        position: relative;

        .info-icon {
          margin-left: 6px;
          width: 14px;
          height: 14px;
          color: rgba(255, 255, 255, 0.5);
          cursor: help;

          &:hover {
            color: #00ccff;
          }
        }
      }

      .icon,
      :deep(.icon svg) {
        margin-right: 6px;
        width: 14px;
        height: 14px;
      }

      .view-all {
        margin-left: auto;
        font-size: 12px;
        font-weight: normal;
        color: rgba(0, 200, 255, 0.8);
        cursor: pointer;

        &:hover {
          color: #00eaff;
          text-decoration: underline;
        }
      }
    }
  }

  .storage-info-grid {
    display: flex;
    align-items: center;

    .usage-chart {
      width: 120px;
      height: 120px;
      position: relative;
      flex-shrink: 0;

      .gauge-chart {
        width: 100%;
        height: 100%;
      }
    }

    .storage-stats {
      flex: 1;
      margin-left: 15px;

      .stat-row {
        display: flex;
        align-items: center;
        margin-bottom: 10px;

        .stat-icon {
          width: 22px;
          height: 22px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 8px;
          flex-shrink: 0;

          .icon-in-circle,
          :deep(.icon-in-circle svg) {
            width: 12px;
            height: 12px;
          }

          &.total-icon {
            background-color: rgba(64, 158, 255, 0.2);
            color: #409eff;
          }

          &.used-icon {
            background-color: rgba(103, 194, 58, 0.2);
            color: #67c23a;
          }

          &.threshold-icon {
            background-color: rgba(230, 162, 60, 0.2);
            color: #e6a23c;
          }
        }

        .stat-content {
          flex: 1;

          .stat-label {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.6);
          }

          .stat-value {
            font-size: 14px;
            font-weight: bold;
            color: #fff;
          }
        }
      }
    }
  }

  .category-stats {
    margin-top: 15px;
    border-top: 1px solid rgba(0, 180, 220, 0.2);
    padding-top: 10px;

    .category-title {
      font-size: 14px;
      color: #00ccff;
      margin-bottom: 10px;
      font-weight: bold;
      display: flex;
      align-items: center;

      .category-icon,
      :deep(.category-icon svg) {
        width: 13px;
        height: 13px;
        margin-right: 5px;
      }
    }

    .category-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
      gap: 8px;

      .category-item {
        background: rgba(0, 30, 60, 0.4);
        padding: 8px;
        border-radius: 4px;
        text-align: center;

        .category-name {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.7);
          margin-bottom: 4px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .category-count {
          font-size: 16px;
          font-weight: bold;
          color: #00eaff;
        }
      }
    }
  }

  .info-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;

    .info-row {
      display: flex;
      align-items: center;
      font-size: 13px;

      &.full-width {
        grid-column: 1 / -1;
      }

      .label {
        color: rgba(255, 255, 255, 0.6);
        margin-right: 8px;
        display: inline-flex;
        align-items: center;
        white-space: nowrap;

        .el-icon,
        :deep(.el-icon svg) {
          margin-right: 4px;
          width: 13px;
          height: 13px;
        }
      }

      .value {
        color: #fff;
        word-break: break-all;

        &.code {
          font-family: monospace;
          background: rgba(0, 0, 0, 0.2);
          padding: 1px 4px;
          border-radius: 3px;
        }

        &.address {
          line-height: 1.4;
        }

        &.website a {
          color: #00aaff;
          text-decoration: none;

          &:hover {
            text-decoration: underline;
          }
        }
      }
    }
  }

  .alerts-container.enhanced {
    .alert-item {
      background: rgba(0, 30, 60, 0.3);
      border-radius: 4px;
      padding: 10px;
      margin-bottom: 10px;
      border-left: 3px solid var(--el-color-primary);
      transition: transform 0.2s ease, box-shadow 0.2s ease;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
      }

      &.high-level {
        border-left-color: #f56c6c;
        background: rgba(245, 108, 108, 0.1);
      }

      &.medium-level {
        border-left-color: #e6a23c;
        background: rgba(230, 162, 60, 0.1);
      }

      &.low-level {
        border-left-color: var(--el-color-primary);
      }

      .alert-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        .alert-time {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.5);
        }
      }

      .alert-message {
        margin: 8px 0;
        font-size: 13px;
        line-height: 1.5;
      }

      .alert-context {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px dashed rgba(255, 255, 255, 0.1);
      }
    }
  }

  .requests-container.enhanced {
    .request-item {
      background: rgba(0, 30, 60, 0.3);
      border-radius: 4px;
      padding: 12px;
      margin-bottom: 10px;
      transition: transform 0.2s ease, box-shadow 0.2s ease;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }

      .request-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;

        .id-container {
          display: flex;
          align-items: center;

          .request-label {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.6);
            margin-right: 5px;
          }

          .request-id {
            font-family: monospace;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.9);
            background: rgba(0, 0, 0, 0.2);
            padding: 2px 6px;
            border-radius: 3px;
          }
        }
      }

      .request-details {
        margin: 10px 0;
        display: flex;
        flex-wrap: wrap;
        gap: 10px;

        .detail-item {
          display: flex;
          align-items: center;
          font-size: 12px;
          color: rgba(255, 255, 255, 0.7);

          .icon-small,
          :deep(.icon-small svg) {
            margin-right: 4px;
            width: 12px;
            height: 12px;
          }
        }
      }

      .request-summary {
        margin-top: 10px;
        border-top: 1px dashed rgba(255, 255, 255, 0.1);
        padding-top: 8px;

        .summary-label {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.6);
          margin-bottom: 6px;
        }

        .summary-items {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;

          .el-tag {
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .more-items {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
            margin-left: 5px;
          }
        }
      }
    }
  }

  .empty-content {
    padding: 20px 0;
    cursor: default;
  }
}
</style>