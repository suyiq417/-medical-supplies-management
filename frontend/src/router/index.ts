import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import { useAuthStore } from "@/stores/auth"; // 请确保路径正确

const router = createRouter({
	history: createWebHistory(import.meta.env.BASE_URL),
	routes: [
		{
			path: "/login",
			name: "login",
			component: () => import("../views/Login.vue"), // 替换为你的登录组件路径
			meta: { public: true }, // 标记为公共页面，无需登录即可访问
		},
		{
			path: "/",
			component: HomeView,
			meta: { requiresAuth: true }, // 访问 HomeView 及其子路由需要登录
			children: [
				{
					// 数据大屏页面使用 index 文件夹下的页面
					path: "",
					name: "index",
					component: () => import("../views/index/index.vue"),
				},
				// 管理模式路由
				{
					// 管理模式下的总览使用 dashboard 文件夹下的页面
					path: "management/dashboard",
					name: "management-dashboard",
					component: () => import("../views/dashboard/index.vue"),
					meta: { requiresAdmin: true },
				},
				{
					path: "management/analysis",
					name: "management-analysis",
					component: () => import("../views/analysis/index.vue"),
					meta: { requiresAdmin: true },
				},
				{
					path: "management/hospitals",
					name: "management-hospitals",
					component: () => import("../views/hospitals/index.vue"),
					meta: { requiresAdmin: true },
				},
				{
					path: "management/hospitals/:id",
					name: "management-hospital-detail",
					component: () => import("../views/hospitals/detail.vue"),
					meta: { requiresAdmin: true },
				},
				{
					path: "management/inventory",
					name: "management-inventory",
					component: () => import("../views/inventory/index.vue"),
					meta: { requiresAdmin: true },
				},
				{
					path: "management/inventory/:id",
					name: "management-inventory-detail",
					component: () => import("../views/inventory/detail.vue"),
					meta: { requiresAdmin: true },
				},
				{
					path: "management/supplies",
					name: "management-supplies",
					component: () => import("../views/supplies/index.vue"),
					meta: { requiresAdmin: true },
				},
				{
					path: "management/supplies/:code",
					name: "management-supplies-detail",
					component: () => import("../views/supplies/detail.vue"),
					meta: { requiresAdmin: true },
				},
				{
					path: "management/suppliers",
					name: "management-suppliers",
					component: () => import("../views/suppliers/index.vue"),
					meta: { requiresAdmin: true },
				},
				{
					path: "management/requests",
					name: "management-requests",
					component: () => import("../views/requests/index.vue"),
					meta: { requiresAdmin: true },
				},
				{
					path: "management/requests/:id",
					name: "management-requests-detail",
					component: () => import("../views/requests/detail.vue"),
					meta: { requiresAdmin: true },
				},
				{
					path: "management/alerts",
					name: "management-alerts",
					component: () => import("../views/alerts/index.vue"),
					meta: { requiresAdmin: true },
				},
				{
					path: "management/alerts/:id",
					name: "management-alerts-detail",
					component: () => import("../views/alerts/detail.vue"),
					meta: { requiresAdmin: true },
				},
			],
		},
	],
});

router.beforeEach((to, from, next) => {
	const authStore = useAuthStore(); // 获取认证 store 实例
	const requiresAuth = !to.meta.public; // 检查路由是否需要认证
	const requiresAdmin = to.meta.requiresAdmin === true; // 检查路由是否需要管理员权限

	if (requiresAuth && !authStore.isAuthenticated) {
		// 如果需要认证但用户未登录，重定向到登录页
		next({ name: "login", query: { redirect: to.fullPath } }); // 保留重定向地址
	} else if (authStore.isAuthenticated && to.name === "login") {
		// 如果用户已登录，但尝试访问登录页，重定向到首页
		next({ name: "index" });
	} else if (requiresAdmin && authStore.userRole !== "admin") {
		// 如果需要管理员权限但用户不是管理员，重定向到数据大屏页
		next({ name: "index" }); // 或者可以重定向到一个 '无权限' 页面
	} else {
		// 其他情况（已登录且有权限，或访问公共页面）允许访问
		next();
	}
});

export default router;
