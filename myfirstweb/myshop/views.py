from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .models import Bike, Rental, Customer, BikeCategory
from datetime import datetime

# def Home (request) :
# return HttpResponse('<h1 > Hello Django : MyShop </h1>')


def Home(request):
    return render(request, "myshop_template/home.html")


def clear_session(request):
    """Clear the booking session and redirect to dates page"""
    request.session.flush()
    return redirect("dates")


def Dates(request):
    # Check if session has expired (older than 10 minutes)
    if "rental_data" in request.session:
        # Session exists, Django will handle expiry via SESSION_COOKIE_AGE
        pass

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
    return render(
        request, "myshop_template/1-dates.html", {"initial_data": initial_data}
    )


def Bikes(request):
    # Check if date info exists
    if "rental_data" not in request.session:
        return redirect("dates")

    if request.method == "POST":
        # Check if category or bike_id was submitted
        category = request.POST.get("category")
        bike_id = request.POST.get("bike_id")

        if category:
            # Category selected - store it and show bikes in that category
            request.session["selected_category"] = category
            request.session.modified = True
            # Stay on bikes page to show bikes in selected category
            return redirect("bikes")
        elif bike_id:
            # Specific bike selected
            request.session["selected_bike_id"] = bike_id
            # Clear category selection since bike is chosen
            if "selected_category" in request.session:
                del request.session["selected_category"]
            request.session.modified = True
            return redirect("customer")

    # Check if user wants to go back to category selection (via GET with clear_category param)
    if request.GET.get("clear_category"):
        if "selected_category" in request.session:
            del request.session["selected_category"]
            request.session.modified = True
        return redirect("bikes")

    # Check if a category was selected
    selected_category = request.session.get("selected_category")

    if selected_category:
        # Get bikes in the selected category from database
        try:
            category = BikeCategory.objects.get(name=selected_category)
            category_bikes = Bike.objects.filter(status="Available", category=category)
            return render(
                request,
                "myshop_template/2-bikes-category.html",
                {"category": selected_category, "bikes": category_bikes},
            )
        except BikeCategory.DoesNotExist:
            # Category doesn't exist, redirect back to category selection
            if "selected_category" in request.session:
                del request.session["selected_category"]
            request.session.modified = True
            return redirect("bikes")

    # No category selected yet - show category selection
    # Get all categories from database
    categories = BikeCategory.objects.all().order_by("price_daily")
    return render(request, "myshop_template/2-bikes.html", {"categories": categories})


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
            "citizen_id": request.POST.get("citizen_id"),
            "line_id": request.POST.get("line_id"),
        }
        request.session.modified = True
        return redirect("checkout")

    return render(
        request, "myshop_template/3-customer.html", {"initial_data": initial_data}
    )


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

    # Calculate rental duration and prices
    from datetime import datetime, timedelta

    pickup_date = datetime.strptime(rental_data["pickup_date"], "%Y-%m-%d")
    return_date = datetime.strptime(rental_data["return_date"], "%Y-%m-%d")

    # Calculate number of days (at least 1 day)
    rental_days = max(1, (return_date - pickup_date).days + 1)

    # Calculate rental price
    rental_price = bike.category.price_daily * rental_days

    # Get deposit amount
    deposit_amount = bike.category.deposit_amount

    # Calculate total price (rental + deposit)
    total_price = rental_price + deposit_amount

    if request.method == "POST":
        # Save everything to DB

        # 1. Create or Get Customer
        customer, created = Customer.objects.get_or_create(
            citizen_id=customer_data["citizen_id"],
            defaults={
                "first_name": customer_data["first_name"],
                "last_name": customer_data["last_name"],
                "phone": customer_data["phone"],
                "email": rental_data["email"],
                "line_id": customer_data["line_id"],
            },
        )
        # Update email if customer already exists
        if not created:
            customer.email = rental_data["email"]
            customer.first_name = customer_data["first_name"]
            customer.last_name = customer_data["last_name"]
            customer.phone = customer_data["phone"]
            customer.line_id = customer_data["line_id"]
            customer.save()

        # 2. Create Rental
        # Combine date and time
        start_str = f"{rental_data['pickup_date']} {rental_data['pickup_time']}"
        end_str = f"{rental_data['return_date']} {rental_data['return_time']}"

        Rental.objects.create(
            start_date=start_str,
            end_date=end_str,
            total_price=total_price,  # Rental price + deposit
            customer=customer,
            bike=bike,
            payment_status="Active",
        )

        # Clear session
        request.session.flush()

        return JsonResponse(
            {"success": True, "message": "Booking Confirmed, Thank you!"}
        )

    return render(
        request,
        "myshop_template/4-checkout.html",
        {
            "rental": rental_data,
            "customer": customer_data,
            "bike": bike,
            "rental_days": rental_days,
            "rental_price": rental_price,
            "deposit_amount": deposit_amount,
            "total_price": total_price,
        },
    )
