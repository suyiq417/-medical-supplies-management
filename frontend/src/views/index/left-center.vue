<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from 'vue-router'; // 导入 useRouter
import { hospitalsOverview } from "@/api/modules/index";
import { ElMessage } from "element-plus";
import type { HospitalsOverview } from "@/types/models";

const router = useRouter(); // 获取 router 实例

const option = ref({});
const data = ref<HospitalsOverview | null>(null);
const loading = ref(false);

const usagePercentage = computed(() => {
  if (data.value && data.value.total_capacity > 0) {
    // 确保 current_usage 存在且为数字，否则视为 0
    const currentUsage = typeof data.value.current_usage === 'number' ? data.value.current_usage : 0;
    return ((currentUsage / data.value.total_capacity) * 100).toFixed(1);
  }
  return '0.0';
});

const getData = async () => {
  loading.value = true;
  try {
    const res = await hospitalsOverview();
    if (res) {
      data.value = res;
      setOption();
    }
  } catch (err) {
    ElMessage.error('获取医院概览数据失败');
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const setOption = () => {
  if (!data.value) return;

  const pieData = data.value.by_level
    .filter(item => item.count > 0)
    .map(item => ({
      name: item.level_display,
      value: item.count
    }));

  option.value = {
    title: {
      text: [`{value|${data.value.total_hospitals}}`, "{name|医院总数}"].join("\n"),
      top: "center",
      left: "center",
      textStyle: {
        rich: {
          value: {
            color: "#ffffff",
            fontSize: 24,
            fontWeight: "bold",
            lineHeight: 20,
            padding: [4, 0, 4, 0]
          },
          name: {
            color: "#ffffff",
            lineHeight: 20,
          },
        },
      },
    },
    tooltip: {
      trigger: "item",
      formatter: "{b} : {c}个 ({d}%)"
    },
    series: [
      {
        name: "医院等级",
        type: "pie",
        radius: ["45%", "70%"],
        center: ['50%', '50%'], // 确保饼图居中
        avoidLabelOverlap: true, // 避免标签重叠
        itemStyle: {
          borderRadius: 6,
          borderColor: "rgba(255,255,255,0.2)",
          borderWidth: 2,
        },
        label: {
          show: true,
          formatter: "  {b|{b}}  \n  {c|{c}个}  {per|{d}%}  ",
          // --- 修改 rich text 样式 ---
          rich: {
            b: { // 医院等级标签
              color: "#fff", // 白色字体
              fontSize: 14, // 增大字体
              fontWeight: 'bold', // 加粗
              lineHeight: 26,
              // 可以考虑添加背景色提高对比度，但可能影响美观
              // backgroundColor: 'rgba(0,0,0,0.3)',
              // padding: [2, 4],
              // borderRadius: 3
            },
            c: { // 数量标签
              color: "#31ABE3",
              fontSize: 14,
            },
            per: { // 百分比标签
              color: "#31ABE3",
              fontSize: 14,
            },
          },
        },
        labelLine: {
          show: true,
          length: 15, // 可以适当调整引线长度
          length2: 25,
          smooth: 0.2,
          lineStyle: { // 调整引线样式
            color: 'rgba(255, 255, 255, 0.5)' // 调暗引线颜色
          }
        },
        data: pieData
      },
    ],
  };
};

const goToHospitals = () => { // 跳转函数
  router.push('/management/hospitals'); // 确认路由路径正确
};

onMounted(() => {
  getData();
});
</script>

<template>
  <!-- --- 修改：在外层 div 添加点击事件和 class --- -->
  <div class="chart-container clickable-area" v-loading="loading" @click="goToHospitals">
    <div v-if="data" class="stats-header">
      <div class="stat-item">
        <div class="stat-value">{{ data.active_hospitals }}</div>
        <div class="stat-label">活跃医院</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ usagePercentage }}%</div>
        <div class="stat-label">库存使用率</div>
      </div>
    </div>
    <v-chart class="chart" :option="option" autoresize /> <!-- 添加 autoresize 使图表自适应容器 -->
  </div>
</template>

<style scoped lang="scss">
.chart-container {
  width: 100%;
  height: 100%;
  position: relative;
  // --- 新增：添加手型光标和过渡效果 ---
  cursor: pointer;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: rgba(255, 255, 255, 0.05); // 悬停时轻微高亮
  }

  .stats-header {
    position: absolute;
    top: 10px;
    left: 0;
    width: 100%;
    display: flex;
    justify-content: space-around;
    z-index: 10; // 确保在图表之上
    pointer-events: none; // 阻止头部统计信息触发点击事件

    .stat-item {
      text-align: center;

      .stat-value {
        font-size: 20px;
        font-weight: bold;
        color: #00fdfa;
      }

      .stat-label {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.7);
      }
    }
  }

  .chart {
    width: 100%;
    height: 100%;
  }
}
</style>
