from django.urls import path
from . import views

urlpatterns = [
    # Bosh sahifa (Landing)
    path('', views.home_view, name='home'),

    # Autentifikatsiya (Client & Umumiy)
    path('auth/register/', views.register_view, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),

    # Super Admin (Loyiha Egasi - /admin/ orqali bitta sahifada login yoki dashboard)
    path('admin/', views.admin_portal_view, name='admin_portal'),
    path('admin/', views.admin_portal_view, name='super_dashboard'),
    path('admin/landing/', views.super_landing_settings_view, name='super_landing_settings'),
    path('admin/storage/', views.super_storage_view, name='super_storage'),
    path('admin/restaurants/', views.super_restaurants_view, name='super_restaurants'),
    path('admin/orders/', views.super_orders_view, name='super_orders'),

    # Restoran Egasi (Client) Kabineti (Barcha restoranlar /r/<slug>/dashboard/ yoki /dashboard/ orqali)
    path('r/<slug:slug>/dashboard/', views.restaurant_portal_view, name='restaurant_portal'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/menu/', views.menu_items_view, name='menu_items'),
    path('dashboard/tables/', views.tables_view, name='tables'),
    path('dashboard/tables/print-all/', views.print_all_tables_qr, name='print_all_tables_qr'),
    path('dashboard/tables/<int:table_id>/print/', views.print_single_table_qr, name='print_single_table_qr'),
    path('dashboard/cashier/', views.cashier_view, name='cashier'),
    path('dashboard/kitchen/', views.kitchen_view, name='kitchen'),
    path('dashboard/history/', views.history_view, name='order_history'),
    path('dashboard/visitors/', views.visitors_view, name='visitors_list'),
    path('dashboard/settings/', views.settings_view, name='settings'),

    # Cashier & Kitchen KDS API
    path('api/sidebar/counts/', views.api_sidebar_badge_counts, name='api_sidebar_badge_counts'),
    path('api/cashier/orders/', views.api_cashier_orders, name='api_cashier_orders'),
    path('api/cashier/orders/<int:order_id>/pay/', views.api_cashier_pay_order, name='api_cashier_pay_order'),
    path('api/kitchen/orders/', views.api_kitchen_orders, name='api_kitchen_orders'),
    path('api/kitchen/orders/<int:order_id>/update/', views.api_kitchen_update_order, name='api_kitchen_update_order'),

    # Mijozlar Menyusi (Mobile formatda QR orqali)
    path('r/<slug:slug>/', views.public_menu_view, name='public_menu'),
    path('r/<slug:slug>/track/', views.api_track_visitor, name='api_track_visitor'),
    path('r/<slug:slug>/order/', views.api_create_order, name='api_create_order'),
    path('api/order/<int:order_id>/status/', views.api_order_status, name='api_order_status'),
]
