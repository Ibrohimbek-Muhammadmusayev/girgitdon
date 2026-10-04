from django.contrib import admin
from .models import Restaurant, Category, MenuItem, DiningTable, Order, OrderItem

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'phone', 'is_active', 'created_at')
    search_fields = ('name', 'owner__username', 'phone')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'order')
    list_filter = ('restaurant',)

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'category', 'price', 'is_available')
    list_filter = ('restaurant', 'category', 'is_available')
    search_fields = ('name',)

@admin.register(DiningTable)
class DiningTableAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'name', 'number')
    list_filter = ('restaurant',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'restaurant', 'table_number', 'status', 'total_price', 'estimated_minutes', 'created_at')
    list_filter = ('restaurant', 'status', 'created_at')
    inlines = [OrderItemInline]
