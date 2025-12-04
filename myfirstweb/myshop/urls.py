# from django.contrib import admin
# from django.urls import path, include

# urlpatterns = [
# path( 'admin/', admin.site.urls),
# path('', include('myshop.urls'))
# ]

from django.urls import path
from .views import Home, Dates, Bikes, CustomerView, Checkout

urlpatterns = [
    path("", Home, name="home"),
    path("dates/", Dates, name="dates"),
    path("bikes/", Bikes, name="bikes"),
    path("customer/", CustomerView, name="customer"),
    path("checkout/", Checkout, name="checkout"),
]
