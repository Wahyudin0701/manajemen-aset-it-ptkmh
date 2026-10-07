from django.contrib import admin
from .models import Employee, Category, Asset, AssetUnit, AssetAssignment

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
    list_display = ('unit_code', 'asset', 'status', 'assigned_to')
    list_filter = ('status',)
    search_fields = ('unit_code', 'asset__name')

@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = ('unit', 'employee', 'assigned_date', 'status')
    list_filter = ('status',)
    search_fields = ('unit__unit_code', 'employee__name')
