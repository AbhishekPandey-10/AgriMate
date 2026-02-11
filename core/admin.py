from django.contrib import admin
from .models import FarmerProfile, CropCycle, Expense, Yield, SchemeRecommendation

@admin.register(FarmerProfile)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ('user', 'farmer_code', 'total_land_area', 'get_free_land')

@admin.register(CropCycle)
class CropAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'crop_name', 'status', 'area_used')
    list_filter = ('status', 'crop_name')

admin.site.register(Expense)
admin.site.register(Yield)

@admin.register(SchemeRecommendation)
class SchemeRecommendationAdmin(admin.ModelAdmin):
    list_display = ('scheme_name', 'farmer', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'farmer')
    search_fields = ('scheme_name', 'description')
    date_hierarchy = 'created_at'

