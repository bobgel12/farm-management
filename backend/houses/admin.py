from django.contrib import admin
from .models import House


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ['farm', 'house_number', 'chicken_in_date', 'chicken_out_date', 'current_day', 'status', 'is_active']
    list_filter = ['farm', 'is_active', 'chicken_in_date']
    search_fields = ['farm__name', 'house_number']
    readonly_fields = ['current_day', 'days_remaining', 'status', 'created_at', 'updated_at']
    list_select_related = ['farm']
