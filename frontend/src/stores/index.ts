import { defineStore } from "pinia";
import type { IndexConfig } from "@/types/settings";

export const useSettingStore = defineStore("setting", {
	state: () => ({
		settingVisible: false,
		defaultOption: {
			singleHeight: 0,
			step: 0.5,
			limitScrollNum: 5,
			hover: true,
			singleWaitTime: 1000,
			wheel: true,
		},
		indexConfig: {
			leftBottomSwiper: true,
			rightBottomSwiper: true,
			showHospitalLabels: true,
			refreshInterval: {
				leftTop: 30,
				leftCenter: 60,
				leftBottom: 60,
				centerMap: 120,
				centerBottom: 60,
				rightTop: 120,
				rightCenter: 60,
				rightBottom: 60,
			},
			searchHistoryLimit: 10,
		} as IndexConfig,
	}),
	actions: {
		setSettingShow(value: boolean) {
			this.settingVisible = value;
		},
		updateIndexConfig(config: Partial<IndexConfig>) {
			this.indexConfig = {
				...this.indexConfig,
				...config,
			};
		},
	},
});
