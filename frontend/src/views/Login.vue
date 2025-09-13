<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '@/stores/auth'; // 导入认证 store
import { User, Lock } from '@element-plus/icons-vue'; // 导入图标
import { POST, AUTH_API } from '@/api/api'; // 导入 POST 辅助函数和 API 定义

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const username = ref('');
const password = ref('');
const loading = ref(false);

const handleLogin = async () => {
    if (!username.value || !password.value) {
        ElMessage.warning('请输入用户名和密码');
        return;
    }

    loading.value = true;
    try {
        // --- 调用实际的登录 API ---
        const response = await POST(AUTH_API.login, { // 使用 AUTH_API.login 获取登录 URL
            username: username.value,
            password: password.value,
        });

        // 假设后端返回 { token: '...', user: { ..., is_staff: true/false } }
        const { token, user } = response; // 直接解构 response

        if (token && user) {
            // 根据 is_staff 判断角色
            const role = user.is_staff ? 'admin' : 'user';
            // 调用 store action 更新状态
            authStore.login(token, role);

            ElMessage.success('登录成功');

            // 检查是否有重定向地址
            const redirectPath = route.query.redirect as string | undefined;
            if (redirectPath) {
                router.push(redirectPath);
            } else {
                // 默认跳转到首页 (数据大屏)
                router.push('/');
            }
        } else {
            // 如果后端返回的数据结构不符合预期
            throw new Error('登录响应格式不正确');
        }
        // --- API 调用结束 ---

    } catch (error: any) {
        console.error('登录失败:', error);
        let errorMessage = '登录失败，请检查用户名或密码';
        if (typeof error === 'string') { // 如果是 reject(error.msg)
            errorMessage = error;
        } else if (error?.response?.status === 400) { // 如果是 reject(error) 且包含 response
            errorMessage = '用户名或密码错误';
        } else if (error?.response?.data?.detail) {
            errorMessage = error.response.data.detail;
        } else if (error instanceof Error) { // 其他 Error 类型
            errorMessage = error.message;
        }

        ElMessage.error(errorMessage);
    } finally {
        loading.value = false;
    }
};
</script>

<template>
    <div class="login-container">
        <div class="login-box">
            <h2 class="login-title">医疗物资管理平台登录</h2>
            <el-form @submit.prevent="handleLogin">
                <el-form-item>
                    <el-input v-model="username" placeholder="用户名" :prefix-icon="User" size="large" clearable />
                </el-form-item>
                <el-form-item>
                    <el-input v-model="password" type="password" placeholder="密码" :prefix-icon="Lock" size="large"
                        show-password clearable @keyup.enter="handleLogin" />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleLogin" :loading="loading" class="login-button" size="large">
                        {{ loading ? '登录中...' : '登 录' }}
                    </el-button>
                </el-form-item>
            </el-form>
        </div>
    </div>
</template>

<style scoped lang="scss">
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background-color: #03050c;
    /* 与 HomeView 背景色一致 */
    background-image: url('../assets/img/bg.jpg');
    /* 可选：添加背景图 */
    background-size: cover;
    background-position: center;
}

.login-box {
    width: 400px;
    padding: 40px;
    background-color: rgba(10, 25, 50, 0.8);
    /* 半透明背景 */
    border-radius: 8px;
    box-shadow: 0 4px 15px rgba(0, 180, 220, 0.2);
    border: 1px solid rgba(0, 180, 220, 0.3);
}

.login-title {
    text-align: center;
    margin-bottom: 30px;
    color: #00fdfa;
    /* 标题颜色 */
    font-size: 24px;
    font-weight: bold;
}

.el-form-item {
    margin-bottom: 25px;
}

/* 输入框样式调整 */
:deep(.el-input__wrapper) {
    background-color: rgba(0, 50, 100, 0.5) !important;
    box-shadow: none !important;
    border: 1px solid rgba(0, 180, 220, 0.4) !important;
}

:deep(.el-input__inner) {
    color: #fff !important;
}

:deep(.el-input__inner::placeholder) {
    color: rgba(255, 255, 255, 0.6);
}

:deep(.el-input__prefix .el-icon),
:deep(.el-input__suffix .el-icon) {
    color: rgba(255, 255, 255, 0.8);
}


.login-button {
    width: 100%;
    background: linear-gradient(90deg, #0072ff, #00eaff);
    border: none;
    color: #fff;
    font-weight: bold;
    transition: all 0.3s ease;

    &:hover {
        opacity: 0.9;
        box-shadow: 0 0 15px rgba(0, 234, 255, 0.5);
    }
}
</style>