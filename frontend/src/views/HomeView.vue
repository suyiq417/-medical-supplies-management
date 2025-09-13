<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import HeaderView from './header.vue';
import { DataBoard, PieChart, HomeFilled, Box, Goods, User, Document, Warning } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();

// 当前导航模式: dashboard(大屏) 或 management(详情管理)
const navMode = computed(() => {
  return route.path.startsWith('/management') ? 'management' : 'dashboard';
});

// 计算当前激活的菜单项
const activeMenu = computed(() => {
  const path = route.path;
  // 详情页面高亮它们的列表页
  if (path.includes('/hospitals/') && !path.endsWith('/hospitals')) {
    return '/management/hospitals';
  } else if (path.includes('/inventory/') && !path.endsWith('/inventory')) {
    return '/management/inventory';
  } else if (path.includes('/supplies/') && !path.endsWith('/supplies')) {
    return '/management/supplies';
  } else if (path.includes('/requests/') && !path.endsWith('/requests')) {
    return '/management/requests';
  } else if (path.includes('/alerts/') && !path.endsWith('/alerts')) {
    return '/management/alerts';
  }
  return path;
});

// 为所有链接更新管理模式下的路径
const getManagementPath = (path: string) => {
  if (path.startsWith('/management/')) return path;
  return `/management${path}`;
};

// 切换到管理模式
const toManagement = () => {
  router.push('/management/dashboard');
};

// 查看详情
const handleDetail = (route: string, id: string) => {
  router.push(getManagementPath(`/${route}/${id}`));
};
</script>

<template>
  <div class="dashboard-container">
    <!-- 头部导航 - 只在管理模式显示 -->
    <header class="management-header" v-if="navMode === 'management'">
      <HeaderView :navMode="navMode" @toDashboard="toManagement" />
    </header>

    <!-- 内容区布局 -->
    <div class="content-layout">
      <!-- 仅在管理模式显示侧边栏 -->
      <div class="sidebar" v-if="navMode === 'management'">
        <div class="logo">
          <h2>应急物资管理系统</h2>
        </div>

        <!-- 导航菜单 -->
        <el-menu :default-active="activeMenu" class="nav-menu" background-color="transparent" text-color="#fff"
          active-text-color="#00fdfa" router>
          <el-menu-item index="/management/dashboard">
            <el-icon>
              <DataBoard />
            </el-icon>
            <span>总览</span>
          </el-menu-item>

          <!-- 其他菜单项保持不变 -->
          <el-menu-item index="/management/analysis">
            <el-icon>
              <PieChart />
            </el-icon>
            <span>数据分析</span>
          </el-menu-item>

          <el-menu-item index="/management/hospitals">
            <el-icon>
              <HomeFilled />
            </el-icon>
            <span>医院管理</span>
          </el-menu-item>

          <el-menu-item index="/management/inventory">
            <el-icon>
              <Box />
            </el-icon>
            <span>库存管理</span>
          </el-menu-item>

          <el-menu-item index="/management/supplies">
            <el-icon>
              <Goods />
            </el-icon>
            <span>物资管理</span>
          </el-menu-item>

          <el-menu-item index="/management/suppliers">
            <el-icon>
              <User />
            </el-icon>
            <span>供应商管理</span>
          </el-menu-item>

          <el-menu-item index="/management/requests">
            <el-icon>
              <Document />
            </el-icon>
            <span>物资调度</span>
          </el-menu-item>

          <el-menu-item index="/management/alerts">
            <el-icon>
              <Warning />
            </el-icon>
            <span>预警管理</span>
          </el-menu-item>
        </el-menu>
      </div>

      <!-- 主内容区 -->
      <div class="main-content"
        :class="{ 'with-sidebar': navMode === 'management', 'dashboard-mode': navMode === 'dashboard' }">
        <!-- 路由视图 -->
        <div class="page-content" :class="{ 'dashboard-content': navMode === 'dashboard' }">
          <router-view />
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
}

.content-layout {
  display: flex;
  flex-direction: row;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 240px;
  background-color: #03050C;
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  z-index: 10;
  height: 100%;
}

.logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}

.logo h2 {
  font-size: 18px;
  margin-top: 8px;
  color: #00fdfa;
}

.nav-menu {
  width: 100%;
  border-right: none;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #03050C;
  overflow: auto;

  &.with-sidebar {
    border-left: 1px solid rgba(0, 180, 220, 0.3);
  }

  &.dashboard-mode {
    padding: 0;
  }
}

.management-header {
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background: linear-gradient(90deg, rgba(0, 20, 45, 0.8) 0%, rgba(0, 100, 150, 0.8) 100%);
  border-bottom: 1px solid rgba(0, 180, 220, 0.3);

  h2 {
    color: #00fdfa;
    margin: 0;
  }
}

.page-content {
  flex: 1;
  padding: 0px;
  overflow-y: auto;

  &.dashboard-content {
    padding: 0;
  }
}

.dashboard-content {
  flex: 1;
  display: flex;
  width: 100%;
  padding: 10px;
  gap: 10px;
}
</style>
