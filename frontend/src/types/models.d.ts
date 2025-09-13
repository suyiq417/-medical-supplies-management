export interface User {
	id: string;
	username: string;
	first_name: string;
	last_name: string;
	email: string;
}

export interface Hospital {
	hospital_id: string;
	org_code: string;
	name: string;
	level: number;
	level_display: string;
	region: string;
	address: string;
	geo_location: {
		type: string;
		coordinates: [number, number];
	};
	storage_volume: number;
	current_capacity: number;
	warning_threshold: number;
	is_active: boolean;
	alerts_count?: number;
	usage_ratio?: number;
	status?: string;
	contact_info?: {
		phone: string;
		email: string;
		website?: string;
	};
	alerts?: InventoryAlert[];
	created_at: string;
	updated_at: string;
}

export interface Supplier {
	supplier_id: string;
	name: string;
	contact_person: string;
	address: string;
	credit_rating: number;
	contact_info?: {
		phone?: string;
		email?: string;
		fax?: string;
		website?: string;
		additional_contacts?: {
			name: string;
			position: string;
			phone: string;
			email: string;
		}[];
		remarks?: string;
	};
	created_at: string;
	updated_at: string;
}

export interface MedicalSupply {
	unspsc_code: string;
	name: string;
	category: string;
	category_display: string;
	description?: string;
	unit: string;
	shelf_life: number;
	storage_temp?: string;
	standard?: string;
	is_controlled: boolean;
	min_stock_level: number;
	avg_price?: number;
	supplier?: Supplier;
	created_at: string;
	updated_at: string;
}

export interface InventoryBatch {
	batch_id: string;
	batch_number: string;
	hospital: Hospital;
	supply: MedicalSupply;
	quantity: number;
	production_date: string;
	expiration_date: string;
	received_date: string;
	received_by?: User;
	quality_check_passed: boolean;
	unit_price?: number;
	supplier?: Supplier;
	storage_condition?: {
		temperature?: string;
		humidity?: string;
		light?: string;
		notes?: string;
	};
	notes?: string;
	created_at: string;
	updated_at: string;
}

export interface RequestItem {
	item_id: string;
	supply: MedicalSupply;
	quantity: number;
	allocated: number;
	notes?: string;
}

export interface SupplyRequest {
	request_id: string;
	hospital: Hospital;
	items: RequestItem[];
	request_time: string;
	required_by: string;
	emergency: boolean;
	priority: number;
	status: string;
	status_display: string;
	requester: User;
	approver?: User;
	approval_time?: string;
	comments?: string;
	created_at: string;
	updated_at: string;
}

export interface InventoryAlert {
	alert_id: string;
	hospital: Hospital;
	alert_type: string;
	alert_type_display: string;
	message: string;
	supply?: MedicalSupply;
	inventory_batch?: InventoryBatch;
	is_resolved: boolean;
	resolved_time?: string;
	resolved_by?: User;
	resolution_notes?: string;
	current_quantity?: number;
	created_at: string;
	updated_at: string;
}

export interface HospitalsOverview {
	total_hospitals: number;
	active_hospitals: number;
	by_level: {
		level: number;
		level_display: string;
		count: number;
	}[];
	total_capacity: number;
	current_usage: number;
}

export interface AlertsOverview {
	total_alerts: number;
	unresolved_alerts: number;
	by_type: {
		alert_type: string;
		alert_type_display: string;
		count: number;
	}[];
	recent_alerts: InventoryAlert[];
}

export interface RequestsOverview {
	total_requests: number;
	emergency_requests: number;
	pending_approval: number;
	by_status: {
		status: string;
		status_display: string;
		count: number;
	}[];
}

// API通用响应结构（如果您的后端返回格式是这样的）
export interface ApiResponse<T> {
	success: boolean;
	code: number;
	message: string;
	data: T;
}

// 分页响应结构
export interface PaginatedResponse<T> {
	count: number;
	next: string | null;
	previous: string | null;
	results: T[];
}
