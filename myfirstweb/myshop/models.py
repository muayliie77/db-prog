from django.db import models

# Create your models here.


class Admin(models.Model):
    ROLE_CHOICES = [
        ("Owner", "Owner"),
        ("Staff", "Staff"),
    ]
    admin_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=50)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="Staff")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'admins'

    def __str__(self):
        return self.username


class BikeCategory(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    price_daily = models.DecimalField(max_digits=10, decimal_places=2)
    price_weekly = models.DecimalField(max_digits=10, decimal_places=2)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'bike_categories'

    def __str__(self):
        return self.name


class Bike(models.Model):
    STATUS_CHOICES = [
        ("Available", "Available"),
        ("Rented", "Rented"),
        ("Fix", "Fix"),
    ]
    bike_id = models.AutoField(primary_key=True)
    license_plate = models.CharField(max_length=20, unique=True)
    model_name = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Available"
    )
    category = models.ForeignKey(BikeCategory, on_delete=models.CASCADE, db_column='category_id')
    description = models.CharField(max_length=1000, blank=True, null=True)
    engine_size = models.CharField(max_length=10, blank=True, null=True)
    image_url = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'bikes'

    def __str__(self):
        return f"{self.model_name} ({self.license_plate})"


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    citizen_id = models.CharField(max_length=13, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=10)
    email = models.CharField(max_length=50)
    line_id = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'customers'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Rental(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("Active", "Active"),
        ("Done", "Done"),
        ("Cancelled", "Cancelled"),
    ]
    rental_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column='customer_id')
    bike = models.ForeignKey(Bike, on_delete=models.CASCADE, db_column='bike_id')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    actual_return_date = models.DateTimeField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Active")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'rentals'

    def __str__(self):
        return f"Rental {self.rental_id} - {self.customer}"
