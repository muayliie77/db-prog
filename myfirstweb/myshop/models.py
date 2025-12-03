from django.db import models

# Create your models here.


class Admin(models.Model):
    ROLE_CHOICES = [
        ("Owner", "Owner"),
        ("Staff", "Staff"),
    ]
    admin_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return self.username


class BikeCategory(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    price_daily = models.DecimalField(max_digits=10, decimal_places=2)
    price_weekly = models.DecimalField(max_digits=10, decimal_places=2)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Bike(models.Model):
    STATUS_CHOICES = [
        ("Available", "Available"),
        ("Rented", "Rented"),
        ("Fix", "Fix"),
    ]
    bike_id = models.AutoField(primary_key=True)
    license_plate = models.CharField(max_length=20)
    model_name = models.CharField(max_length=100)
    color = models.CharField(max_length=50)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Available"
    )
    category = models.ForeignKey(BikeCategory, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.model_name} ({self.license_plate})"


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    passport_id = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    line_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Rental(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Done", "Done"),
    ]
    rental_id = models.AutoField(primary_key=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    actual_return_date = models.DateTimeField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_delivery = models.BooleanField(default=False)
    delivery_address = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    bike = models.ForeignKey(Bike, on_delete=models.CASCADE)

    def __str__(self):
        return f"Rental {self.rental_id} - {self.customer}"
