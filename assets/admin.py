from django.contrib import admin
from .models import (
    Employee, Category, Asset, AssetUnit, AssetAssignment,
    ConfigurationItem, CIHistory, ConsumableItem, ConsumableTransaction
)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('nik', 'name')
    search_fields = ('nik', 'name')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('asset_code', 'name', 'category', 'qty')
    list_filter = ('category',)
    search_fields = ('asset_code', 'name')

@admin.register(AssetUnit)
class AssetUnitAdmin(admin.ModelAdmin):
    list_display = ('unit_code', 'serial_number', 'asset', 'status', 'assigned_to')
    list_filter = ('status',)
    search_fields = ('unit_code', 'serial_number', 'asset__name')

@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = ('unit', 'employee', 'assigned_date', 'status')
    list_filter = ('status',)
    search_fields = ('unit__unit_code', 'employee__name')

@admin.register(ConfigurationItem)
class ConfigurationItemAdmin(admin.ModelAdmin):
    list_display = ('ci_code', 'name', 'category', 'status', 'condition', 'installed_on', 'assigned_to')
    list_filter = ('category', 'status', 'condition')
    search_fields = ('ci_code', 'name', 'serial_number')

@admin.register(CIHistory)
class CIHistoryAdmin(admin.ModelAdmin):
    list_display = ('ci', 'action', 'related_unit', 'related_employee', 'timestamp')
    list_filter = ('action',)
    search_fields = ('ci__ci_code', 'ci__name')

@admin.register(ConsumableItem)
class ConsumableItemAdmin(admin.ModelAdmin):
    list_display = ('item_code', 'name', 'category', 'stock_available', 'base_unit', 'minimum_stock', 'location')
    list_filter = ('category', 'location')
    search_fields = ('item_code', 'name', 'brand', 'specification')

@admin.register(ConsumableTransaction)
class ConsumableTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_code', 'transaction_type', 'item', 'quantity', 'unit', 'quantity_base', 'stock_after', 'transaction_date')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('transaction_code', 'item__name', 'ticket_number')
