// filepath: c:\Users\suyiq\Desktop\mywork\frontend2\src\stores\auth.ts
import { defineStore } from "pinia";
import { ref } from "vue";

export const useAuthStore = defineStore("auth", () => {
	// 示例状态：根据你的实际需求修改
	const isAuthenticated = ref(false); // 或者从 localStorage 初始化
	const userRole = ref<string | null>(null); // 'admin', 'user', or null
	const token = ref<string | null>(localStorage.getItem("authToken")); // 示例 token

	// 示例：从 localStorage 初始化状态
	if (token.value) {
		isAuthenticated.value = true;
		// 你可能需要从 token 解析角色或在登录时保存角色
		userRole.value = localStorage.getItem("userRole");
	}

	// 示例 Action：登录
	function login(newToken: string, role: string) {
		localStorage.setItem("authToken", newToken);
		localStorage.setItem("userRole", role);
		token.value = newToken;
		userRole.value = role;
		isAuthenticated.value = true;
		// 可能需要调用 API 获取更详细的用户信息
	}

	// 示例 Action：登出
	function logout() {
		localStorage.removeItem("authToken");
		localStorage.removeItem("userRole");
		token.value = null;
		userRole.value = null;
		isAuthenticated.value = false;
	}

	return {
		isAuthenticated,
		userRole,
		token,
		login,
		logout,
	};
});
