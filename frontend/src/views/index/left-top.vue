<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import CapsuleChart from "@/components/datav/capsule-chart";
import { ElMessage } from "element-plus";
import { suppliesOverview } from "@/api/modules/index";
import { useRouter } from "vue-router";
import { Loading, ArrowRight } from '@element-plus/icons-vue'; // 确保导入了 Loading 和 ArrowRight

const router = useRouter();
const config = ref({
  colors: ['#00fdfa', '#0072ff', '#ffd000', '#ff5722', '#07f7a8'],
  unit: "",
  showValue: true,
  showUnit: true,
  axisVisible: false,
  showBottomValue: false,
  labelVisible: true,
  barStyle: {
    borderRadius: 15,
    height: '12px',
    margin: '8px 0'
  },
  valueStyle: {
    fontSize: 14,
    color: '#fff',
    fontWeight: 600
  },
  labelStyle: {
    fontSize: 14,
    color: '#e8e8e8'
  }
});

const loading = ref(false);
const data = ref<any[]>([]);
const totalSupplies = ref(0);
const controlledSupplies = ref(0);
const lowStockSupplies = ref(0);

// 获取物资概览数据
const getData = async () => {
  loading.value = true;
  try {
    const res = await suppliesOverview();
    if (res) {
      totalSupplies.value = res.total_supplies;
      controlledSupplies.value = res.controlled_supplies;
      lowStockSupplies.value = res.low_stock_supplies;

      // 转换分类数据为胶囊图表格式，并使用正确的单位
      data.value = res.by_category.map((item: any) => {
        // 根据物资类别设置不同的单位
        let unit = '个';
        if (item.category === 'DV') unit = '台';
        else if (item.category === 'PP') unit = '套';

        return {
          name: item.category_display,
          value: item.count,
          unit: unit
        };
      }).sort((a: { value: number }, b: { value: number }) => b.value - a.value);
    }
  } catch (error) {
    console.error(error);
    ElMessage.error('物资数据加载失败');
  } finally {
    loading.value = false;
  }
};

// 跳转到物资管理页面
const goToSupplies = () => {
  router.push('/management/supplies');
};

// 定时刷新
let timer: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  getData();
  timer = setInterval(getData, 30000);
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
});
</script>

<template>
  <div class="left-top clickable-area" @click="goToSupplies">
    <div class="summary-cards">
      <div class="card">
        <div class="card-value">{{ totalSupplies }}</div>
        <div class="card-label">物资总数</div>
      </div>
      <div class="card">
        <div class="card-value">{{ controlledSupplies }}</div>
        <div class="card-label">受控物资</div>
      </div>
      <div class="card danger">
        <div class="card-value">{{ lowStockSupplies }}</div>
        <div class="card-label">低库存物资</div>
      </div>
    </div>

    <div class="chart-wrapper">
      <div class="chart-loading" v-if="loading">
        <el-icon class="is-loading">
          <loading />
        </el-icon>
      </div>
      <CapsuleChart :config="config" :data="data" class="capsule-chart" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.clickable-area {
  cursor: pointer;
  /* 添加手型光标 */
  transition: background-color 0.2s ease;
  /* 可选：添加点击反馈效果 */

  &:hover {
    background-color: rgba(255, 255, 255, 0.05);
    /* 可选：悬停时轻微高亮 */
  }
}

.left-top {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;

  .summary-cards {
    display: flex;
    justify-content: space-between;
    margin-bottom: 15px;

    .card {
      flex: 1;
      text-align: center;
      background: rgba(0, 180, 220, 0.1);
      border-radius: 4px;
      padding: 10px;
      margin: 0 5px;

      &.danger {
        background: rgba(204, 0, 51, 0.1);

        .card-value {
          color: #cc0033;
        }
      }

      .card-value {
        font-size: 22px;
        font-weight: bold;
        color: #00fdfa;
        margin-bottom: 5px;
      }

      .card-label {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.7);
      }
    }
  }

  .chart-wrapper {
    flex: 1;
    position: relative;

    .chart-loading {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      color: #fff;
      font-size: 24px;
    }

    .capsule-chart {
      width: 100%;
      height: 100%;
    }
  }
}
</style>