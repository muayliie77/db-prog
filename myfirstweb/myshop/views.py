from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Bike, Rental, Customer, BikeCategory
from datetime import datetime

# def Home (request) :
# return HttpResponse('<h1 > Hello Django : MyShop </h1>')


def Home(request):
    return render(request, "myshop_template/home.html")


def Dates(request):
    initial_data = request.session.get("rental_data", {})
    if request.method == "POST":
        # Save form data to session
        request.session["rental_data"] = {
            "email": request.POST.get("email"),
            "pickup_date": request.POST.get("pickup_date"),
            "pickup_time": request.POST.get("pickup_time"),
            "return_date": request.POST.get("return_date"),
            "return_time": request.POST.get("return_time"),
        }
        request.session.modified = True
        return redirect("bikes")
    return render(request, "myshop_template/1-dates.html", {"initial_data": initial_data})


def Bikes(request):
    # Check if date info exists
    if "rental_data" not in request.session:
        return redirect("dates")

    if request.method == "POST":
        bike_id = request.POST.get("bike_id")
        if bike_id:
            request.session["selected_bike_id"] = bike_id
            request.session.modified = True
        return redirect("customer")

    # Fetch available bikes
    # In a real app, filter by availability for the specific dates
    bikes = Bike.objects.filter(status="Available")

    return render(request, "myshop_template/2-bikes.html", {"bikes": bikes})


def CustomerView(request):
    if (
        "rental_data" not in request.session
        or "selected_bike_id" not in request.session
    ):
        return redirect("dates")

    initial_data = request.session.get("customer_data", {})

    if request.method == "POST":
        request.session["customer_data"] = {
            "first_name": request.POST.get("first_name"),
            "last_name": request.POST.get("last_name"),
            "phone": request.POST.get("phone"),
            "passport_id": request.POST.get("passport_id"),
            "line_id": request.POST.get("line_id"),
        }
        request.session.modified = True
        return redirect("checkout")

    return render(request, "myshop_template/3-customer.html", {"initial_data": initial_data})


def Checkout(request):
    if (
        "rental_data" not in request.session
        or "selected_bike_id" not in request.session
        or "customer_data" not in request.session
    ):
        return redirect("dates")

    rental_data = request.session["rental_data"]
    customer_data = request.session["customer_data"]
    bike_id = request.session["selected_bike_id"]

    bike = Bike.objects.get(pk=bike_id)

    if request.method == "POST":
        # Save everything to DB

        # 1. Create or Get Customer
        customer, created = Customer.objects.get_or_create(
            email=rental_data["email"],
            defaults={
                "first_name": customer_data["first_name"],
                "last_name": customer_data["last_name"],
                "phone": customer_data["phone"],
                "passport_id": customer_data["passport_id"],
                "line_id": customer_data["line_id"],
            },
        )

        # 2. Create Rental
        # Combine date and time
        start_str = f"{rental_data['pickup_date']} {rental_data['pickup_time']}"
        end_str = f"{rental_data['return_date']} {rental_data['return_time']}"

        # Basic price calculation (placeholder logic)
        # Assuming daily price for simplicity
        price = bike.category.price_daily

        Rental.objects.create(
            start_date=start_str,
            end_date=end_str,
            total_price=price,  # This should be calculated based on duration
            customer=customer,
            bike=bike,
            status="Active",
        )

        # Clear session
        request.session.flush()

        return HttpResponse("<h1>Booking Confirmed! Thank you.</h1>")

    return render(
        request,
        "myshop_template/4-checkout.html",
        {"rental": rental_data, "customer": customer_data, "bike": bike},
    )
