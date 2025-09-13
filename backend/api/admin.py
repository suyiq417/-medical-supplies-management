from django.contrib import admin
from .models import (
    Hospital, Supplier, MedicalSupply, InventoryBatch, 
    SupplyRequest, RequestItem, ItemFulfillment, InventoryAlert
)

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'org_code', 'level', 'region', 'is_active')
    list_filter = ('level', 'region', 'is_active')
    search_fields = ('name', 'org_code', 'address')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'credit_rating')
    list_filter = ('credit_rating',)
    search_fields = ('name', 'contact_person')

@admin.register(MedicalSupply)
class MedicalSupplyAdmin(admin.ModelAdmin):
    list_display = ('name', 'unspsc_code', 'category', 'unit', 'is_controlled')
    list_filter = ('category', 'is_controlled')
    search_fields = ('name', 'unspsc_code', 'description')

@admin.register(InventoryBatch)
class InventoryBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'hospital', 'supply', 'quantity', 'expiration_date')
    list_filter = ('hospital', 'received_date', 'quality_check_passed')
    search_fields = ('batch_number', 'supply__name')
    date_hierarchy = 'expiration_date'

@admin.register(SupplyRequest)
class SupplyRequestAdmin(admin.ModelAdmin):
    list_display = ('request_id', 'hospital', 'status', 'priority', 'requester', 'emergency')
    list_filter = ('status', 'priority', 'emergency', 'hospital')
    search_fields = ('request_id', 'hospital__name', 'requester__username')
    date_hierarchy = 'required_by'

@admin.register(RequestItem)
class RequestItemAdmin(admin.ModelAdmin):
    list_display = ('request', 'supply', 'quantity', 'allocated')
    list_filter = ('supply__category',)
    search_fields = ('request__request_id', 'supply__name')

@admin.register(ItemFulfillment)
class ItemFulfillmentAdmin(admin.ModelAdmin):
    list_display = ('request_item', 'inventory_batch', 'quantity', 'fulfilled_by')
    list_filter = ('fulfilled_time',)
    search_fields = ('request_item__request__request_id', 'inventory_batch__batch_number')

@admin.register(InventoryAlert)
class InventoryAlertAdmin(admin.ModelAdmin):
    list_display = ('hospital', 'supply', 'alert_type', 'is_resolved', 'created_at')
    list_filter = ('alert_type', 'is_resolved', 'hospital')
    search_fields = ('hospital__name', 'supply__name', 'message')
    date_hierarchy = 'created_at'
