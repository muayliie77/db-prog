from django.urls import path
from . import admin_views

urlpatterns = [
    path('login/', admin_views.AdminLogin, name='admin_login'),
    path('logout/', admin_views.AdminLogout, name='admin_logout'),
    path('dashboard/', admin_views.AdminDashboard, name='admin_dashboard'),
    path('customers/', admin_views.CustomerList, name='admin_customers'),
    path('bookings/', admin_views.BookingList, name='admin_bookings'),
    path('vehicles/', admin_views.VehicleList, name='admin_vehicles'),
    path('vehicles/create/', admin_views.CreateModel, name='admin_create_model'),
    path('vehicles/add-inventory/', admin_views.AddInventory, name='admin_add_inventory'),
    path('vehicles/<int:bike_id>/edit/', admin_views.EditVehicle, name='admin_edit_vehicle'),
    path('vehicles/<int:bike_id>/delete/', admin_views.DeleteVehicle, name='admin_delete_vehicle'),
    path('vehicle/<int:bike_id>/status/', admin_views.UpdateStatus, name='admin_update_status'),
]

