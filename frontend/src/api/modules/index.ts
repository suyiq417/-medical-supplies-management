import { GET, POST, PUT, DELETE } from "../api";
import {
	ALERTS_API,
	HOSPITALS_API,
	INVENTORY_API,
	SUPPLIES_API,
	SUPPLIERS_API,
	REQUESTS_API,
} from "../api";
import type { SupplyRequest, RequestItem } from "@/types/models";

// 预警相关API
export const getInventoryAlertsList = (params?: any) => {
	return GET(ALERTS_API.list, params || {});
};

export const getAlertDetail = (id: string) => {
	return GET(ALERTS_API.detail(id), {});
};

export const resolveAlertById = (id: string) => {
	return POST(ALERTS_API.resolve(id), {});
};

// 医院相关API
export const getHospitals = (params?: any) => {
	return GET(HOSPITALS_API.list, params || {});
};

// 修改后的医院详情API函数，合并了两个函数的功能
export const getHospitalDetail = (id: string, params?: any) => {
	return GET(HOSPITALS_API.detail(id), params || {});
};

export const hospitalsOverview = () => {
	return GET(HOSPITALS_API.overview, {});
};

export const hospitalsMap = () => {
	return GET(HOSPITALS_API.map, {});
};

/**
 * 获取医院预警信息
 * @param hospitalId 医院ID
 */
export function getHospitalAlerts(hospitalId: string) {
	return GET(ALERTS_API.list, {
		hospital_id: hospitalId,
		is_resolved: "false", // 将布尔值改为字符串
	});
}

/**
 * 获取医院库存信息
 * @param hospitalId 医院ID
 */
export function getHospitalInventory(hospitalId: string) {
	return GET(INVENTORY_API.batches, {
		hospital_id: hospitalId,
		page_size: 10,
	});
}

/**
 * 获取医院物资请求记录
 * @param hospitalId 医院ID
 */
export function getHospitalRequests(hospitalId: string) {
	return GET(REQUESTS_API.list, {
		hospital_id: hospitalId,
		page_size: 5,
	});
}

// 库存相关API
export const getInventoryBatches = (params?: any) => {
	return GET(INVENTORY_API.batches, params || {});
};

export const getInventoryBatchDetail = (id: string) => {
	return GET(INVENTORY_API.batchDetail(id), {});
};

export const inventoryOverview = () => {
	return GET(INVENTORY_API.overview, {});
};

// 物资相关API
export const getSupplies = (params?: any) => {
	return GET(SUPPLIES_API.list, params || {});
};

export const getSupplyDetail = (code: string) => {
	return GET(SUPPLIES_API.detail(code), {});
};

export const suppliesOverview = () => {
	return GET(SUPPLIES_API.overview, {});
};

// 供应商相关API
export const getSuppliers = (params?: any) => {
	return GET(SUPPLIERS_API.list, params || {});
};

export const getSupplierDetail = (id: string) => {
	return GET(SUPPLIERS_API.detail(id), {});
};

// 请求相关API
export const getSupplyRequests = (params?: any) => {
	return GET(REQUESTS_API.list, params || {});
};

export const getRequestDetail = (id: string) => {
	return GET(REQUESTS_API.detail(id), {});
};

/**
 * 批准物资请求 (调用自定义 action)
 * @param requestId 请求的 ID
 */
export function approveRequest(
	requestId: string | number
): Promise<SupplyRequest> {
	return POST(REQUESTS_API.approve(String(requestId)), {});
}

/**
 * 拒绝物资请求 (调用自定义 action)
 * @param requestId 请求的 ID
 */
export function rejectRequest(
	requestId: string | number
): Promise<SupplyRequest> {
	return POST(REQUESTS_API.reject(String(requestId)), {});
}

/**
 * 更新物资请求项的分配数量 (调用自定义 action)
 * @param requestId 父请求的 ID
 * @param itemId 请求项的 ID (来自 RequestItem 模型)
 * @param allocatedQuantity 新的分配数量
 */
export function updateRequestItemAllocation(
	requestId: string | number,
	itemId: string | number,
	allocatedQuantity: number
): Promise<RequestItem> {
	// 使用 POST 调用自定义分配接口
	return POST(REQUESTS_API.allocate_item(String(requestId)), {
		item_id: itemId, // 将 item_id 和 allocated_quantity 作为请求体发送
		allocated_quantity: allocatedQuantity,
	});
}

/**
 * 获取待分配的物资请求项列表
 * @param params 包含筛选和分页参数，例如 { supply_code: '...', request__hospital_id: '...', page: 1, page_size: 10, ordering: '-request__priority' }
 */
export const getRequestItemsForAllocation = (params?: any) => {
	// 调用新的后端端点 /api/allocation-items/
	return GET('/api/allocation-items/', params || {});
};

export const requestStatus = () => {
	return GET(REQUESTS_API.status, {});
};

export function requestFulfillment() {
	return GET(REQUESTS_API.fulfillment, {});
}

export const alertTrends = () => {
	return GET(REQUESTS_API.trends, {});
};

export const inventoryAlerts = () => {
	return GET(ALERTS_API.overview, {});
};
