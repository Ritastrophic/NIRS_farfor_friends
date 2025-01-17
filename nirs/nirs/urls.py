from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from nirs_app import views

personal_patterns = [
    path("", views.user_personal, name='user_personal'),
    path('update/', views.user_update_view, name='user_update'),
    path('delete/', views.user_delete_view, name='user_delete'), 
    path('purchases/', views.my_purchases_view, name='my_purchases'), 
    path('orders/', views.my_orders_view, name='my_orders'),
    path('seller-schedule/', views.my_seller_schedule_view, name='seller_schedule'),
    path('master-schedule/', views.my_master_schedule_view, name='master_schedule'),
]

client_patterns = [
    path("", views.clients_list_view, name='clients_list'),
    path("create/", views.client_create_view, name='client_create'),
    path("<int:id>/", views.client_detail_admin_view, name='client_detail_admin'),
    
]

seller_patterns = [
    path("", views.sellers_list_view, name='sellers_list'),
    path("create/", views.seller_create_view, name='seller_create'),
    path("<int:id>/", views.seller_detail_admin_view, name='seller_detail_admin'),
    path("delete/<int:pk>/", views.seller_delete_view, name='seller_delete'),
]

master_patterns = [
    path("", views.masters_list_view, name='masters_list'),
    path("<int:id>/", views.master_detail_admin_view, name='master_detail_admin'),
    path("create/", views.master_create_view, name='master_create'),
    path("delete/<int:pk>/", views.master_delete_view, name='master_delete'),
]


product_patterns = [
    path("", views.products_list_view, name='products_list'),
    path("create/", views.product_create_view, name='product_create'),
    path('update/<int:id>/', views.product_update_view, name='product_update'),
    path("<int:id>/", views.product_detail_admin_view, name='product_detail_admin'),
    path('delete/<int:id>/', views.product_delete_view, name='product_delete'),
]

service_patterns = [
    path("", views.services_list_view, name='services_list'),
    path("create/", views.service_create_view, name='service_create'),
    path('update/<int:id>/', views.service_update_view, name='service_update'),
    path("<int:id>/", views.service_detail_admin_view, name='service_detail_admin'),
    path('delete/<int:id>/', views.service_delete_view, name='service_delete'),
]

material_patterns = [
    path("", views.materials_list_view, name='materials_list'),
    path("create/", views.material_create_view, name='material_create'),
    path('update/<int:id>/', views.material_update_view, name='material_update'),
    path("<int:id>/", views.material_detail_admin_view, name='material_detail_admin'),
    path('delete/<int:id>/', views.material_delete_view, name='material_delete'),
]

workshop_patterns = [
    path("", views.workshops_list_view, name='workshops_list'),
    path("create/", views.workshop_create_view, name='workshop_create'),
    path('update/<int:id>/', views.workshop_update_view, name='workshop_update'),
    path("<int:id>/", views.workshop_detail_admin_view, name='workshop_detail_admin'),
    path('delete/<int:id>/', views.workshop_delete_view, name='workshop_delete'),
]


sale_patterns = [
    path("", views.sales_list_view, name='sales_list'),
    path("create/", views.sale_create_view, name='sale_create'),
    path('update/<int:id>/', views.sale_update_view, name='sale_update'),
    path("<int:id>/", views.sale_detail_admin_view, name='sale_detail_admin'),
    path('delete/<int:id>/', views.sale_delete_view, name='sale_delete'),
]

order_patterns = [
    path("", views.orders_list_view, name='orders_list'),
    path("create/", views.appointment_order_create_view, name='order_create'),
    path('update/<int:order_id>/', views.order_update_view, name='order_update'),
    path("<int:order_id>/", views.order_detail_admin_view, name='order_detail_admin'),
    path('delete/<int:order_id>/', views.order_delete_view, name='order_delete'),
]

supply_patterns = [
 path("", views.supplies_list_view, name='supplies_list'),
    path("create/", views.supply_create_view, name='supply_create'),
    path('update/<int:supply_id>/', views.supply_update_view, name='supply_update'),
    path("<int:id>/", views.supply_detail_admin_view, name='supply_detail_admin'),
    path('delete/<int:id>/', views.supply_delete_view, name='supply_delete'),
]


statistic_pattern = [
    path("", views.stats_view, name='stats'),
    path("products/", views.products_stats_view, name='products_stats'),
    path("services/", views.services_stats_view, name='services_stats'),
    path('sales/', views.sales_stats_view, name='sales_stats'),
]


seller_schedule_patterns = [
    path('', views.seller_schedules_view, name='seller_schedules'),
    path('create/', views.create_seller_schedules, name='create_seller_schedules'),
    path('add/', views.seller_schedule_add_view, name='seller_schedule_add'),
    path('<int:pk>/', views.seller_schedule_detail_view, name='seller_schedule_detail'),
    path('<int:pk>/update/', views.seller_schedule_update_view, name='seller_schedule_update'),
    path('<int:pk>/delete/', views.seller_schedule_delete_view, name='seller_schedule_delete'), 
]

master_schedules_patterns = [
    path('', views.master_schedules_view, name='master_schedules'),
    path('create/', views.create_master_schedules, name='create_master_schedules'),
    path('add/', views.master_schedule_add_view, name='master_schedule_add'),
    path('<int:pk>/', views.master_schedule_detail_view, name='master_schedule_detail'),
    path('<int:pk>/update/', views.master_schedule_update_view, name='master_schedule_update'),
    path('<int:pk>/delete/', views.master_schedule_delete_view, name='master_schedule_delete'), 
]


urlpatterns = [
    path("", views.index, name='home'),
    path("about/", views.about, name='about'),
    path("contacts/", views.contacts, name='contacts'),

    path('create_superuser/', views.create_superuser_view, name='create_superuser'),

    path("auth/", views.auth_view, name='auth'),
    path("registration/", views.client_registration_view, name='client_registration'),
    path("logout/", views.logout_view, name='logout'),

    path("personal/", include(personal_patterns)),

    path("cart/", views.cart_view, name='user_cart'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('update_cart_item/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout, name='checkout'),


    path('booking/', views.booking_view, name='booking_view'),
    path('create_booking/', views.create_booking, name='create_booking'),
    path('get-workshops/', views.get_workshops, name='get_workshops'), # добавленный URL
    path('get-masters/', views.get_masters, name='get_masters'),  # добавленный URL
    path('get-available-times/', views.get_available_times, name='get_available_times'), # добавленный URL
    path('api/get_service/<int:service_id>/', views.get_service, name='get_service'),
    path('api/get_additional_services/', views.get_additional_services, name='get_additional_services'),

    path('seller_schedules/', include(seller_schedule_patterns)),
    path('master_schedules/', include(master_schedules_patterns)),

    path("our_products/", views.products_view, name='products'),
    path("our_services/", views.services_view, name='services'),
    path("our_masters/", views.masters_view, name='masters'),
    path("our_workshops/", views.workshops_view, name='workshops'),

    path("our_products/<int:id>/", views.product_detail_view, name='product_detail'),
    path("our_services/<int:id>/", views.service_detail_view, name='service_detail'),
    path("our_masters/<int:id>/", views.master_detail_view, name='master_detail'),
    path("our_workshops/<int:id>/", views.workshop_detail_view, name='workshop_detail'),

    path("client/", include(client_patterns)),
    path("seller/", include(seller_patterns)),
    path("master/", include(master_patterns)),


    path("products/", include(product_patterns)),
    path("services/", include(service_patterns)),
    path("workshops/", include(workshop_patterns)),
    path("materials/", include(material_patterns)),


    path("sales/", include(sale_patterns)),
    path("orders/", include(order_patterns)),
    path("supplies/", include(supply_patterns)),

    path("stats/", include(statistic_pattern)),

    path("admin/",views.admin_main, name='admin_main'),
    path("seller_main/", views.seller_main, name='seller_main'),
    path("master_main/", views.master_main, name='master_main')

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)