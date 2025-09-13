<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { ElInput, ElTag, ElMessage } from 'element-plus';
import { Search } from '@element-plus/icons-vue';
import { getHospitals } from '@/api/modules/index';
import { useSettingStore } from "@/stores";
import { storeToRefs } from "pinia";
import type { Hospital } from '@/types/models';

// 定义事件
const emit = defineEmits(['search']);

// 获取设置
const settingStore = useSettingStore();
const { indexConfig } = storeToRefs(settingStore);

// 搜索相关数据
const searchValue = ref('');
const searchHistory = ref<string[]>([]);
const hospitals = ref<Hospital[]>([]);
const loading = ref(false);

// 初始化加载医院列表
const loadHospitals = async () => {
  loading.value = true;
  try {
    const res = await getHospitals({ page_size: 20 });
    if (res) {
      hospitals.value = res.results || res;
    }
  } catch (err) {
    console.error(err);
    ElMessage.error('加载医院列表失败');
  } finally {
    loading.value = false;
  }
};

// 搜索建议列表
const filterHospitals = computed(() => {
  if (!searchValue.value) return [];

  return hospitals.value.filter(hospital =>
    hospital.name.toLowerCase().includes(searchValue.value.toLowerCase())
  );
});

// 处理搜索
const handleSearch = async () => {
  if (!searchValue.value) return;

  // 更新搜索历史
  if (!searchHistory.value.includes(searchValue.value)) {
    searchHistory.value.unshift(searchValue.value);

    // 限制历史记录数量
    const limit = 10; // Using a direct default value since indexConfig doesn't have searchHistoryLimit
    if (searchHistory.value.length > limit) {
      searchHistory.value = searchHistory.value.slice(0, limit);
    }
  }

  // 找到对应的医院
  const foundHospital = hospitals.value.find(h =>
    h.name.toLowerCase().includes(searchValue.value.toLowerCase())
  );

  if (foundHospital) {
    emit('search', {
      id: foundHospital.hospital_id,
      name: foundHospital.name
    });
  } else {
    // 如果没找到，通过API查询
    try {
      loading.value = true;
      const res = await getHospitals({ name: searchValue.value });
      if (res && (res.results?.length > 0 || res.length > 0)) {
        const searchResults = res.results || res;
        emit('search', {
          id: searchResults[0].hospital_id,
          name: searchResults[0].name
        });
      } else {
        ElMessage.warning('未找到匹配的医院');
      }
    } catch (err) {
      console.error(err);
      ElMessage.error('搜索医院失败');
    } finally {
      loading.value = false;
    }
  }
};

// 点击历史记录
const handleHistoryClick = (item: string) => {
  searchValue.value = item;
  handleSearch();
};

// 点击建议项
const handleSuggestionClick = (hospital: Hospital) => {
  searchValue.value = hospital.name;
  emit('search', {
    id: hospital.hospital_id,
    name: hospital.name
  });

  // 更新搜索历史
  if (!searchHistory.value.includes(hospital.name)) {
    searchHistory.value.unshift(hospital.name);

    // 限制历史记录数量
    const limit = 10; // Using default value as searchHistoryLimit doesn't exist in indexConfig
    if (searchHistory.value.length > limit) {
      searchHistory.value = searchHistory.value.slice(0, limit);
    }
  }
};

// 删除历史记录
const removeHistory = (item: string) => {
  const index = searchHistory.value.indexOf(item);
  searchHistory.value.splice(index, 1);
};

// 清空历史记录
const clearHistory = () => {
  searchHistory.value = [];
};

// 加载本地存储的历史记录
const loadSearchHistory = () => {
  const savedHistory = localStorage.getItem('hospital-search-history');
  if (savedHistory) {
    try {
      searchHistory.value = JSON.parse(savedHistory);
    } catch (e) {
      console.error('解析搜索历史失败', e);
    }
  }
};

// 保存历史记录到本地存储
const saveSearchHistory = () => {
  localStorage.setItem('hospital-search-history', JSON.stringify(searchHistory.value));
};

// 监听历史记录变化，保存到本地存储
watch(searchHistory, () => {
  saveSearchHistory();
}, { deep: true });

onMounted(() => {
  loadSearchHistory();
  loadHospitals();
});
</script>

<template>
  <div class="search-container">
    <div class="search-header">
      <ElInput v-model="searchValue" placeholder="请输入医院名称" :prefix-icon="Search" clearable @keyup.enter="handleSearch"
        :loading="loading">
        <template #append>
          <el-button @click="handleSearch">搜索</el-button>
        </template>
      </ElInput>
    </div>

    <!-- 搜索建议 -->
    <div v-if="searchValue && filterHospitals.length" class="search-suggestions">
      <div v-for="hospital in filterHospitals" :key="hospital.hospital_id" class="suggestion-item"
        @click="handleSuggestionClick(hospital)">
        <div class="hospital-name">{{ hospital.name }}</div>
        <div class="hospital-info">
          <span class="hospital-level">{{ hospital.level_display }}</span>
          <span class="hospital-region">{{ hospital.region }}</span>
        </div>
      </div>
    </div>

    <!-- 搜索历史 -->
    <div v-if="searchHistory.length" class="search-history">
      <div class="history-header">
        <span>搜索历史</span>
        <el-button link @click="clearHistory">清空</el-button>
      </div>
      <div class="history-tags">
        <ElTag v-for="item in searchHistory" :key="item" closable @click="handleHistoryClick(item)"
          @close="removeHistory(item)">
          {{ item }}
        </ElTag>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.search-container {
  padding: 16px;
  height: 100%;

  .search-header {
    margin-bottom: 16px;
  }

  .search-suggestions {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
    margin-top: 8px;
    max-height: 200px;
    overflow-y: auto;

    &::-webkit-scrollbar {
      width: 5px;
    }

    &::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.2);
      border-radius: 3px;
    }

    .suggestion-item {
      padding: 8px 16px;
      cursor: pointer;
      color: #fff;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);

      &:last-child {
        border-bottom: none;
      }

      &:hover {
        background: rgba(0, 0, 0, 0.3);
      }

      .hospital-name {
        font-weight: bold;
        margin-bottom: 5px;
      }

      .hospital-info {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.7);
        display: flex;
        gap: 10px;
      }
    }
  }

  .search-history {
    margin-top: 16px;

    .history-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      color: rgba(255, 255, 255, 0.7);
    }

    .history-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;

      .el-tag {
        cursor: pointer;
        background: rgba(0, 0, 0, 0.2);
        border-color: rgba(255, 255, 255, 0.1);
        color: #fff;
      }
    }
  }
}
</style>