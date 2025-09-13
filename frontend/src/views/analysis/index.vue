<script setup lang="ts">
import { ref, onMounted } from 'vue';
import * as echarts from 'echarts';
import { alertTrends, requestStatus, hospitalsOverview, suppliesOverview } from '@/api/modules/index';
import { ElMessage } from 'element-plus';

// 图表引用
const supplyChartRef = ref<HTMLElement | null>(null);
const hospitalChartRef = ref<HTMLElement | null>(null);
const alertChartRef = ref<HTMLElement | null>(null);
const requestChartRef = ref<HTMLElement | null>(null);

// 图表实例
let supplyChart: echarts.ECharts | null = null;
let hospitalChart: echarts.ECharts | null = null;
let alertChart: echarts.ECharts | null = null;
let requestChart: echarts.ECharts | null = null;

// 加载状态
const loading = ref({
  supplies: false,
  hospitals: false,
  alerts: false,
  requests: false
});

// 初始化物资分类图表
const initSupplyChart = async () => {
  loading.value.supplies = true;
  try {
    const res = await suppliesOverview();
    if (!res) throw new Error('获取物资数据失败');

    if (supplyChartRef.value) {
      supplyChart = echarts.init(supplyChartRef.value);
      
      const option = {
        title: {
          text: '物资类别分布',
          left: 'center',
          textStyle: {
            color: '#fff'
          }
        },
        tooltip: {
          trigger: 'item'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          textStyle: {
            color: '#fff'
          }
        },
        series: [
          {
            type: 'pie',
            radius: '50%',
            data: res.by_category.map((item: any) => ({
              name: item.category_display,
              value: item.count
            })),
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            },
            label: {
              color: '#fff'
            }
          }
        ]
      };
      
      supplyChart.setOption(option);
    }
  } catch (err) {
    console.error(err);
    ElMessage.error('获取物资数据失败');
  } finally {
    loading.value.supplies = false;
  }
};

// 初始化医院等级图表
const initHospitalChart = async () => {
  loading.value.hospitals = true;
  try {
    const res = await hospitalsOverview();
    if (!res) throw new Error('获取医院数据失败');

    if (hospitalChartRef.value) {
      hospitalChart = echarts.init(hospitalChartRef.value);
      
      const option = {
        title: {
          text: '医院等级分布',
          left: 'center',
          textStyle: {
            color: '#fff'
          }
        },
        tooltip: {
          trigger: 'item'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          textStyle: {
            color: '#fff'
          }
        },
        series: [
          {
            type: 'pie',
            radius: '50%',
            data: res.by_level.map((item: any) => ({
              name: item.level_display,
              value: item.count
            })),
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            },
            label: {
              color: '#fff'
            }
          }
        ]
      };
      
      hospitalChart.setOption(option);
    }
  } catch (err) {
    console.error(err);
    ElMessage.error('获取医院数据失败');
  } finally {
    loading.value.hospitals = false;
  }
};

// 初始化预警趋势图表
const initAlertChart = async () => {
  loading.value.alerts = true;
  try {
    const res = await alertTrends();
    if (!res) throw new Error('获取预警趋势数据失败');

    if (alertChartRef.value) {
      alertChart = echarts.init(alertChartRef.value);
      
      const series = res.datasets.map((dataset: any) => ({
        name: dataset.type_display,
        type: 'line',
        data: dataset.data,
        smooth: true
      }));
      
      const option = {
        title: {
          text: '预警趋势分析',
          left: 'center',
          textStyle: {
            color: '#fff'
          }
        },
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: res.datasets.map((item: any) => item.type_display),
          top: 30,
          textStyle: {
            color: '#fff'
          }
        },
        xAxis: {
          type: 'category',
          data: res.labels,
          axisLabel: {
            color: '#fff'
          }
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            color: '#fff'
          }
        },
        series: series
      };
      
      alertChart.setOption(option);
    }
  } catch (err) {
    console.error(err);
    ElMessage.error('获取预警趋势数据失败');
  } finally {
    loading.value.alerts = false;
  }
};

// 初始化请求状态图表
const initRequestChart = async () => {
  loading.value.requests = true;
  try {
    const res = await requestStatus();
    if (!res) throw new Error('获取请求状态数据失败');

    if (requestChartRef.value) {
      requestChart = echarts.init(requestChartRef.value);
      
      const option = {
        title: {
          text: '物资请求状态统计',
          left: 'center',
          textStyle: {
            color: '#fff'
          }
        },
        tooltip: {
          trigger: 'item'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          textStyle: {
            color: '#fff'
          }
        },
        series: [
          {
            type: 'pie',
            radius: '50%',
            data: res.by_status.map((item: any) => ({
              name: item.status_display,
              value: item.count
            })),
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            },
            label: {
              color: '#fff'
            }
          }
        ]
      };
      
      requestChart.setOption(option);
    }
  } catch (err) {
    console.error(err);
    ElMessage.error('获取请求状态数据失败');
  } finally {
    loading.value.requests = false;
  }
};

// 处理窗口调整
const handleResize = () => {
  supplyChart?.resize();
  hospitalChart?.resize();
  alertChart?.resize();
  requestChart?.resize();
};

onMounted(() => {
  initSupplyChart();
  initHospitalChart();
  initAlertChart();
  initRequestChart();
  
  window.addEventListener('resize', handleResize);
  
  return () => {
    window.removeEventListener('resize', handleResize);
    supplyChart?.dispose();
    hospitalChart?.dispose();
    alertChart?.dispose();
    requestChart?.dispose();
  };
});
</script>

<template>
  <div class="analysis-container">
    <div class="chart-row">
      <div class="chart-card">
        <div v-if="loading.supplies" class="loading">
          <el-icon class="is-loading"><loading /></el-icon>
          <span>加载中...</span>
        </div>
        <div ref="supplyChartRef" class="chart"></div>
      </div>
      
      <div class="chart-card">
        <div v-if="loading.hospitals" class="loading">
          <el-icon class="is-loading"><loading /></el-icon>
          <span>加载中...</span>
        </div>
        <div ref="hospitalChartRef" class="chart"></div>
      </div>
    </div>
    
    <div class="chart-row">
      <div class="chart-card">
        <div v-if="loading.alerts" class="loading">
          <el-icon class="is-loading"><loading /></el-icon>
          <span>加载中...</span>
        </div>
        <div ref="alertChartRef" class="chart"></div>
      </div>
      
      <div class="chart-card">
        <div v-if="loading.requests" class="loading">
          <el-icon class="is-loading"><loading /></el-icon>
          <span>加载中...</span>
        </div>
        <div ref="requestChartRef" class="chart"></div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.analysis-container {
  padding: 20px;
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  gap: 20px;
  
  .chart-row {
    display: flex;
    gap: 20px;
    flex: 1;
    
    .chart-card {
      flex: 1;
      background: rgba(0, 20, 45, 0.7);
      border: 1px solid rgba(0, 180, 220, 0.3);
      border-radius: 4px;
      box-shadow: 0 0 10px rgba(0, 180, 220, 0.1);
      padding: 15px;
      position: relative;
      
      .chart {
        width: 100%;
        height: 100%;
      }
      
      .loading {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 20, 45, 0.8);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: #fff;
        z-index: 10;
        
        .el-icon {
          font-size: 24px;
          margin-bottom: 10px;
        }
      }
    }
  }
}
</style>
