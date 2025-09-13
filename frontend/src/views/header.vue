<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount } from "vue";
import dayjs from 'dayjs';
import type { DateDataType } from "./index.d"
import { useRouter, useRoute } from 'vue-router';
import { DataBoard, Setting, SwitchButton } from '@element-plus/icons-vue'; // 导入退出图标
import { useAuthStore } from '@/stores/auth'; // 导入认证状态管理 store
import { ElMessageBox, ElMessage } from 'element-plus'; // 引入 ElMessageBox 和 ElMessage

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore(); // 获取 authStore 实例

// 当前导航模式: dashboard(大屏) 或 management(详情管理)
const navMode = computed(() => {
  return route.path.startsWith('/management') ? 'management' : 'dashboard';
});

// 切换到大屏模式
const toDashboard = () => {
  router.push('/');
};

// 切换到管理模式
const toManagement = () => {
  router.push('/management/dashboard');
};

// 使用ref而不是reactive可以提高性能
const currentTime = ref("");
const currentWeek = ref("");
const timer = ref<number | null>(null);

const weekday = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]

// 更高效的时间更新函数
const updateTime = () => {
  const now = dayjs();
  currentTime.value = now.format("YYYY-MM-DD HH:mm:ss");
  currentWeek.value = weekday[now.day()];
};

// 在组件挂载时初始化
onMounted(() => {
  // 立即更新一次时间
  updateTime();
  // 然后设置定时器
  timer.value = window.setInterval(updateTime, 1000);
});

// 在组件卸载前清除定时器
onBeforeUnmount(() => {
  if (timer.value) {
    clearInterval(timer.value);
    timer.value = null;
  }
});

// 退出登录处理
const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    authStore.logout();
    router.push('/login');
    ElMessage.success('已退出登录');
  }).catch(() => {
    // 用户取消操作
  });
};
</script>

<template>
  <div class="title_wrap">
    <div class="zuojuxing"></div>
    <div class="youjuxing"></div>
    <div class="guang"></div>

    <div class="header-content">
      <!-- 导航模式切换按钮 -->
      <div class="left-section">
        <div class="nav-buttons">
          <el-button class="nav-button" :class="{ 'active': navMode === 'dashboard' }" @click="toDashboard">
            <el-icon>
              <DataBoard />
            </el-icon>
            <span>数据大屏</span>
          </el-button>
          <el-button v-if="authStore.userRole === 'admin'" class="nav-button"
            :class="{ 'active': navMode === 'management' }" @click="toManagement">
            <el-icon>
              <Setting />
            </el-icon>
            <span>详情管理</span>
          </el-button>
        </div>
      </div>

      <!-- 中间标题 -->
      <div class="center-section">
        <div class="title">
          <span class="title-text">武汉市医疗物资管理平台</span>
        </div>
      </div>

      <!-- 右侧时间与退出按钮 -->
      <div class="right-section">
        <div class="timers">
          <span>{{ currentWeek }} {{ currentTime }}</span>
        </div>
        <!-- 修改退出登录按钮 -->
        <el-button @click="handleLogout" class="logout-btn-custom" size="small" title="退出登录">
          <el-icon>
            <SwitchButton />
          </el-icon>
          <span>退出</span>
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.title_wrap {
  height: 60px;
  background-image: url("../assets/img/top.png");
  background-size: cover;
  background-position: center center;
  position: relative;
  margin-bottom: 4px;
  width: 100%;
  box-sizing: border-box !important;
}

.header-content {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
  z-index: 15;
  box-sizing: border-box !important;
}

.left-section {
  position: fixed !important;
  /* 使用fixed替代absolute */
  left: 20px !important;
  top: 12px !important;
  /* 设置固定的顶部距离 */
  height: 36px !important;
  display: flex;
  align-items: center;
  z-index: 100 !important;
}

.nav-buttons {
  display: flex;
  gap: 12px;
}

/* 自定义按钮样式，确保一致性 */
.nav-button {
  height: 36px !important;
  padding: 0 16px !important;
  border-radius: 4px !important;
  font-size: 14px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.3s !important;
  border: 1px solid rgba(0, 253, 250, 0.5) !important;
  background-color: rgba(0, 50, 100, 0.3) !important;
  color: #fff !important;

  &.active {
    background-color: rgba(0, 150, 220, 0.5) !important;
    border-color: #00fdfa !important;
    color: #00fdfa !important;
  }

  &:hover {
    background-color: rgba(0, 100, 190, 0.5) !important;
    border-color: #00fdfa !important;
  }

  .el-icon {
    margin-right: 6px;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  span {
    display: inline-block;
    line-height: 1;
  }
}

.center-section {
  flex: 1;
  display: flex;
  justify-content: center;
}

/* 右侧区域 */
.right-section {
  position: fixed !important;
  right: 20px !important;
  top: 12px !important;
  height: 36px !important;
  display: flex;
  align-items: center;
  z-index: 100 !important;
  gap: 15px;
}

.timers {
  font-size: 18px;
  color: #a0cfff; // 调整时间颜色使其柔和
  text-shadow: 0 0 3px rgba(0, 180, 220, 0.3);
  display: flex;
  align-items: center;
}

/* 自定义退出按钮样式 */
.logout-btn-custom {
  height: 32px !important; // 调整高度以匹配小尺寸
  padding: 0 12px !important;
  border-radius: 4px !important;
  font-size: 14px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.3s !important;
  border: 1px solid rgba(255, 70, 89, 0.5) !important; // 使用淡红色边框
  background-color: rgba(255, 70, 89, 0.15) !important; // 使用淡红色背景
  color: rgba(255, 130, 140, 0.9) !important; // 使用稍亮的红色文字

  .el-icon {
    margin-right: 4px;
    font-size: 16px;
  }

  span {
    display: inline-block;
    line-height: 1;
  }

  &:hover {
    border-color: rgba(255, 70, 89, 0.8) !important;
    background-color: rgba(255, 70, 89, 0.3) !important;
    color: #ff6b7d !important; // 悬停时更亮的红色
  }

  &:active {
    border-color: rgba(255, 70, 89, 1) !important;
    background-color: rgba(255, 70, 89, 0.4) !important;
  }
}

.guang {
  position: absolute;
  bottom: -26px;
  background-image: url("../assets/img/guang.png");
  background-position: 80px center;
  width: 100%;
  height: 56px;
  z-index: 1;
}

.zuojuxing,
.youjuxing {
  position: absolute;
  top: -2px;
  width: 140px;
  height: 6px;
  background-image: url("../assets/img/headers/juxing1.png");
  z-index: 1;
}

.zuojuxing {
  left: 11%;
}

.youjuxing {
  right: 11%;
  transform: rotate(180deg);
}
</style>
