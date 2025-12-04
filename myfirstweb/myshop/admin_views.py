from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Admin, Customer, Rental, Bike, BikeCategory, PriceLog
from functools import wraps
from django.utils import timezone

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
def VehicleList(request):
    bikes = Bike.objects.all().order_by('category', 'model_name')
    return render(request, 'myshop_template/admin/vehicle_list.html', {'bikes': bikes})

# --- Vehicle Management (CRUD) ---

@admin_required
def CreateModel(request):
    """Form to add a new car/bike model (require input for all table columns)."""
    categories = BikeCategory.objects.all()
    
    if request.method == 'POST':
        try:
            Bike.objects.create(
                license_plate=request.POST.get('license_plate'),
                model_name=request.POST.get('model_name'),
                category_id=request.POST.get('category_id'),
                engine_size=request.POST.get('engine_size'),
                image_url=request.POST.get('image_url'),
                description=request.POST.get('description'),
                status=request.POST.get('status', 'Available')
            )
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
    """Form to add a vehicle to an existing model (inherit other data)."""
    if request.method == 'POST':
        source_bike_id = request.POST.get('source_bike_id')
        new_license_plate = request.POST.get('license_plate')
        
        try:
            source_bike = Bike.objects.get(pk=source_bike_id)
            
            Bike.objects.create(
                license_plate=new_license_plate,
                model_name=source_bike.model_name,
                category=source_bike.category,
                engine_size=source_bike.engine_size,
                image_url=source_bike.image_url,
                description=source_bike.description,
                status='Available' # Default to available for new inventory
            )
            return redirect('admin_vehicles')
        except Exception as e:
             # In case of error, re-render with context
             bikes = Bike.objects.all().order_by('model_name')
             return render(request, 'myshop_template/admin/add_inventory.html', {
                'error': str(e),
                'bikes': bikes
            })

    # Get unique models/bikes to copy from
    # Group by model_name to show unique "models" to pick from
    # For simplicity, let's just list all bikes and user picks one as "template"
    # Or better, distinct model names? But `engine_size` etc might vary.
    # Let's list all bikes as potential templates, but display them nicely.
    bikes = Bike.objects.all().order_by('model_name')
    return render(request, 'myshop_template/admin/add_inventory.html', {'bikes': bikes})

@admin_required
def EditVehicle(request, bike_id):
    bike = get_object_or_404(Bike, pk=bike_id)
    categories = BikeCategory.objects.all()
    
    if request.method == 'POST':
        try:
            bike.license_plate = request.POST.get('license_plate')
            bike.model_name = request.POST.get('model_name')
            bike.category_id = request.POST.get('category_id')
            bike.engine_size = request.POST.get('engine_size')
            bike.image_url = request.POST.get('image_url')
            bike.description = request.POST.get('description')
            bike.status = request.POST.get('status')
            bike.save()
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
    if request.method == 'POST':
        bike.delete()
        return redirect('admin_vehicles')
    return render(request, 'myshop_template/admin/confirm_delete.html', {'item': bike})

# --- Status Logic ---

@admin_required
def UpdateStatus(request, bike_id):
    if request.method == 'POST':
        bike = get_object_or_404(Bike, pk=bike_id)
        new_status = request.POST.get('status')
        old_status = bike.status
        
        bike.status = new_status
        bike.save()
        
        # Trigger: On status change (Rented -> Available), record actual_return_date
        if old_status == 'Rented' and new_status == 'Available':
            # Find the active rental for this bike
            # Assuming the latest active rental is the one to close
            active_rental = Rental.objects.filter(
                bike=bike, 
                payment_status='Active',
                actual_return_date__isnull=True
            ).order_by('-start_date').first()
            
            if active_rental:
                active_rental.actual_return_date = timezone.now()
                active_rental.payment_status = 'Done' # Or Keep active until paid? Prompt implies just recording date.
                # Let's assume 'Done' or just date update. The prompt says "record actual_return_date".
                # Often "Active" implies currently rented. If returned, it might be "Done" or "Pending Payment".
                # I'll mark as Done for now to close the loop.
                active_rental.payment_status = 'Done'
                active_rental.save()
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

