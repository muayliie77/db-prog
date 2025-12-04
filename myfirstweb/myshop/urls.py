from django.urls import path, include
from .views import Home, Dates, Bikes, CustomerView, Checkout, clear_session

urlpatterns = [
    path("", Home, name="home"),
    path("dates/", Dates, name="dates"),
    path("bikes/", Bikes, name="bikes"),
    path("customer/", CustomerView, name="customer"),
    path("checkout/", Checkout, name="checkout"),
    path("clear-session/", clear_session, name="clear_session"),
    path("shop-admin/", include("myshop.admin_urls")),
]
