from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Admin, Customer, Rental, Bike, BikeCategory, PriceLog
from functools import wraps
from django.utils import timezone
from django.db import connection

# --- Authentication ---

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'admin_id' not in request.session:
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def AdminLogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            admin = Admin.objects.get(username=username, password=password)
            request.session['admin_id'] = admin.admin_id
            request.session['admin_role'] = admin.role
            request.session['admin_username'] = admin.username
            return redirect('admin_dashboard')
        except Admin.DoesNotExist:
            return render(request, 'myshop_template/admin/login.html', {'error': 'Invalid credentials'})
            
    return render(request, 'myshop_template/admin/login.html')

def AdminLogout(request):
    if 'admin_id' in request.session:
        del request.session['admin_id']
    if 'admin_role' in request.session:
        del request.session['admin_role']
    if 'admin_username' in request.session:
        del request.session['admin_username']
    return redirect('admin_login')

# --- Dashboard & Views ---

@admin_required
def AdminDashboard(request):
    # Basic stats
    total_bikes = Bike.objects.count()
    available_bikes = Bike.objects.filter(status='Available').count()
    active_rentals = Rental.objects.filter(payment_status='Active').count()
    
    context = {
        'total_bikes': total_bikes,
        'available_bikes': available_bikes,
        'active_rentals': active_rentals
    }
    return render(request, 'myshop_template/admin/dashboard.html', context)

@admin_required
def CustomerList(request):
    customers = Customer.objects.all().order_by('-created_at')
    return render(request, 'myshop_template/admin/customer_list.html', {'customers': customers})

@admin_required
def BookingList(request):
    rentals = Rental.objects.all().order_by('-created_at')
    return render(request, 'myshop_template/admin/booking_list.html', {'rentals': rentals})

@admin_required
def CompleteBooking(request, rental_id):
    if request.method == 'POST':
        try:
            # Use Stored Procedure: AdminReturnBike
            # AdminReturnBike(p_rental_id)
            # This sets actual_return_date to NOW() and payment_status to 'Done'
            # Trigger trg_bike_returned will set bike status to 'Available'
            
            with connection.cursor() as cursor:
                cursor.execute("CALL AdminReturnBike(%s)", [rental_id])
                
            # Return success (if called via AJAX) or redirect
            # Assuming this is called via form submission or AJAX
            # Let's support redirection for now as it's simpler
            return redirect('admin_bookings')
        except Exception as e:
            # Ideally show error message
            print(f"Error completing booking: {e}")
            return redirect('admin_bookings')
    
    return redirect('admin_bookings')

@admin_required
def VehicleList(request):
    bikes = Bike.objects.all().order_by('category', 'model_name')
    return render(request, 'myshop_template/admin/vehicle_list.html', {'bikes': bikes})

# --- Vehicle Management (CRUD) ---

@admin_required
def CreateModel(request):
    """Form to add a new car/bike model using Stored Procedure."""
    categories = BikeCategory.objects.all()
    
    if request.method == 'POST':
        try:
            # Use Stored Procedure: AdminAddBike
            # AdminAddBike(p_model_name, p_license_plate, p_category_name, p_description, p_engine_size, p_image_url)
            
            # Need category NAME, not ID for the procedure as currently written in SQL dump
            category_id = request.POST.get('category_id')
            category = BikeCategory.objects.get(pk=category_id)
            
            with connection.cursor() as cursor:
                cursor.execute("CALL AdminAddBike(%s, %s, %s, %s, %s, %s)", [
                    request.POST.get('model_name'),
                    request.POST.get('license_plate'),
                    category.name,
                    request.POST.get('description'),
                    request.POST.get('engine_size'),
                    request.POST.get('image_url')
                ])
            
            return redirect('admin_vehicles')
        except Exception as e:
            return render(request, 'myshop_template/admin/vehicle_form.html', {
                'error': str(e),
                'categories': categories,
                'title': 'Create New Model'
            })

    return render(request, 'myshop_template/admin/vehicle_form.html', {
        'categories': categories,
        'title': 'Create New Model'
    })

@admin_required
def AddInventory(request):
    """Form to add a vehicle to an existing model using Stored Procedure."""
    if request.method == 'POST':
        source_bike_id = request.POST.get('source_bike_id')
        new_license_plate = request.POST.get('license_plate')
        
        try:
            # Get the model name from the source bike
            source_bike = Bike.objects.get(pk=source_bike_id)
            
            # Use Stored Procedure: AdminAddBikeFromExisting
            # AdminAddBikeFromExisting(p_model_name, p_new_license_plate)
            
            with connection.cursor() as cursor:
                cursor.execute("CALL AdminAddBikeFromExisting(%s, %s)", [
                    source_bike.model_name,
                    new_license_plate
                ])
                
            return redirect('admin_vehicles')
        except Exception as e:
             # In case of error, re-render with context
             bikes = Bike.objects.all().order_by('model_name')
             return render(request, 'myshop_template/admin/add_inventory.html', {
                'error': str(e),
                'bikes': bikes
            })

    # Get unique models/bikes to copy from
    bikes = Bike.objects.all().order_by('model_name')
    return render(request, 'myshop_template/admin/add_inventory.html', {'bikes': bikes})

@admin_required
def EditVehicle(request, bike_id):
    bike = get_object_or_404(Bike, pk=bike_id)
    categories = BikeCategory.objects.all()
    
    if request.method == 'POST':
        try:
            # Use Stored Procedure: AdminUpdateBikeInfo
            # AdminUpdateBikeInfo(p_bike_id, p_new_model, p_new_plate, p_new_category_name, p_new_description, p_new_engine_size, p_new_image_url)
            
            category_id = request.POST.get('category_id')
            category = BikeCategory.objects.get(pk=category_id)
            
            with connection.cursor() as cursor:
                cursor.execute("CALL AdminUpdateBikeInfo(%s, %s, %s, %s, %s, %s, %s)", [
                    bike_id,
                    request.POST.get('model_name'),
                    request.POST.get('license_plate'),
                    category.name,
                    request.POST.get('description'),
                    request.POST.get('engine_size'),
                    request.POST.get('image_url')
                ])
                
            # Handle status change separately
            new_status = request.POST.get('status')
            # Only update status if it's provided and different
            # Note: If status is 'Rented', the form might not send it (disabled select), so we skip
            if new_status and new_status != bike.status:
                 with connection.cursor() as cursor:
                    cursor.execute("CALL AdminUpdateBikeStatus(%s, %s)", [bike_id, new_status])

            return redirect('admin_vehicles')
        except Exception as e:
            return render(request, 'myshop_template/admin/vehicle_form.html', {
                'error': str(e),
                'bike': bike,
                'categories': categories,
                'title': 'Edit Vehicle'
            })

    return render(request, 'myshop_template/admin/vehicle_form.html', {
        'bike': bike,
        'categories': categories,
        'title': 'Edit Vehicle'
    })

@admin_required
def DeleteVehicle(request, bike_id):
    bike = get_object_or_404(Bike, pk=bike_id)
    
    # Check for existing rentals before attempting deletion
    has_rentals = Rental.objects.filter(bike_id=bike_id).exists()
    
    if request.method == 'POST':
        # Double-check status and rentals before deletion
        if bike.status == 'Rented':
            return render(request, 'myshop_template/admin/confirm_delete.html', {
                'item': bike, 
                'error': 'Cannot delete bike: Bike is currently rented. Please return the bike first.'
            })
        
        if has_rentals:
            return render(request, 'myshop_template/admin/confirm_delete.html', {
                'item': bike, 
                'error': 'Cannot delete bike: This bike has rental history. Bikes with rental records cannot be deleted to maintain data integrity.'
            })
        
        try:
            # Use Stored Procedure: AdminDeleteBike
            # AdminDeleteBike(p_bike_id)
            with connection.cursor() as cursor:
                cursor.execute("CALL AdminDeleteBike(%s)", [bike_id])
            return redirect('admin_vehicles')
        except Exception as e:
             # If delete fails (e.g. trigger prevents deleting rented bike), show error
             error_msg = str(e)
             # Check if it's a foreign key constraint error
             if 'foreign key' in error_msg.lower() or 'cannot delete' in error_msg.lower() or 'rental' in error_msg.lower():
                 error_msg = 'Cannot delete bike: This bike has rental history. Bikes with rental records cannot be deleted to maintain data integrity.'
             return render(request, 'myshop_template/admin/confirm_delete.html', {
                 'item': bike, 
                 'error': error_msg
             })
             
    return render(request, 'myshop_template/admin/confirm_delete.html', {
        'item': bike,
        'has_rentals': has_rentals
    })

# --- Status Logic ---

@admin_required
def UpdateStatus(request, bike_id):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        try:
            # Just a normal status update (e.g. Available -> Fix)
            # Use Stored Procedure: AdminUpdateBikeStatus
            # AdminUpdateBikeStatus(p_bike_id, p_new_status)
            with connection.cursor() as cursor:
                cursor.execute("CALL AdminUpdateBikeStatus(%s, %s)", [bike_id, new_status])
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
            
    return JsonResponse({'success': False}, status=400)
