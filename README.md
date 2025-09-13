# 医疗物资智慧管理平台

本项目是一个前后端分离的医疗物资智慧管理平台，旨在提供数据可视化大屏展示和后台管理功能，用于监控和管理医疗物资的库存、请求、预警等信息。

## 项目结构

```
mywork/
├── backend/         # 后端 Django 项目
│   ├── api/
│   ├── config/
│   ├── manage.py
│   └── README.md    # 后端详细说明
├── frontend/       # 前端 Vue 项目
│   ├── public/
│   ├── src/
│   ├── index.html
│   ├── vite.config.ts
│   └── README.md    # 前端详细说明
└── README.md        # 本文件 (项目根 README)
```

## 模块说明

### 1. 后端 (Backend)

- **位置:** [`backend/`](backend/)
- **描述:** 基于 Django 和 Django REST Framework 构建的 API 服务，负责数据处理、业务逻辑和数据库交互。
- **主要功能:**
  - 机构管理 (医院、供应商)
  - 物资管理 (基础信息、库存批次)
  - 流程管理 (物资请求、审批、分配)
  - 库存预警与监控
  - 数据可视化接口
  - 用户认证
- **技术栈:** Django, Django REST Framework, Django GIS, MySQL (with GIS), GDAL
- **详细说明:** 请参考 [`backend/README.md`](backend/README.md)

### 2. 前端 (Frontend)

- **位置:** [`frontend2/`](frontend2/)
- **描述:** 基于 Vue 3 和 Element Plus 构建的用户界面，包括数据大屏和后台管理系统。
- **主要功能:**
  - **数据大屏:** 物资总览、医院分布地图、库存预警、请求履行计划、医院详情等可视化展示。
  - **后台管理:** 仪表盘、数据分析、医院/物资/库存/供应商/请求/预警的增删改查管理。
  - 用户登录与权限控制。
- **技术栈:** Vue 3, TypeScript, Vite, Pinia, Vue Router, Element Plus, ECharts, 百度地图 GL, Axios, Tailwind CSS
- **详细说明:** 请参考 [`frontend2/README.md`](frontend2/README.md)

## 快速开始

### 1. 启动后端服务

```bash
cd backend
# (根据 backend/README.md 完成环境准备、依赖安装、数据库配置和迁移)
python manage.py runserver
```

详细步骤请参见 [`backend/README.md`](backend/README.md)。

### 2. 启动前端应用

```bash
cd frontend2
# (根据 frontend2/README.md 完成环境准备和依赖安装)
# (确保 .env 文件中 VITE_API_BASE_URL 指向后端服务地址)
pnpm run dev
```

详细步骤请参见 [`frontend2/README.md`](frontend2/README.md)。

## 注意事项

- 确保后端服务正常运行，并且前端配置的 API 地址正确。
- 详细的环境配置、依赖安装和数据导入请分别参考前后端的 README 文件。
