from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    username = None
    first_name = models.CharField(max_length=43)
    last_name = models.CharField(max_length=43)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    is_employee = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING, related_name='seller')
    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

class Master(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING, related_name='master')
    experience_since = models.DateField(null=True)
    photo = models.ImageField(upload_to="images/masters", default="images/masters/no_photo.png")
    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'
    
    def get_photo_url(self):
        if self.photo:
            return self.photo.url
        return f"{settings.MEDIA_URL}images/masters/no_photo.png"

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING, related_name='client')
    birth_date = models.DateField(null=True)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'


class Schedule(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.IntegerField(default=10)
    # Другие поля расписания
    def __str__(self):
        return f"Расписание: {self.start_time} - {self.end_time}"

class SellerSchedule(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.DO_NOTHING)
    schedule = models.ForeignKey(Schedule, on_delete=models.DO_NOTHING)

    class Meta:
        unique_together = ('seller', 'schedule')
        
    def __str__(self):
        return f"{self.seller.user.first_name} {self.seller.user.last_name} - {self.schedule.start_time} - {self.schedule.end_time}"

class MasterSchedule(models.Model):
    master = models.ForeignKey(Master, on_delete=models.DO_NOTHING)
    schedule = models.ForeignKey(Schedule, on_delete=models.DO_NOTHING)

    class Meta:
        unique_together = ('master', 'schedule')
        
    def __str__(self):
        return f"{self.master.user.first_name} {self.master.user.last_name} - {self.schedule.start_time} - {self.schedule.end_time}"


class Product(models.Model):
    photo = models.ImageField(upload_to="images/products", default="images/products/no_photo.png")
    name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    current_quantity = models.IntegerField()

    def __str__(self):
        return self.name
    
    def get_photo_url(self):
        if self.photo:
            return f"{settings.STATIC_URL}{self.photo}"
        return f"{settings.STATIC_URL}images/products/no_photo.png"

class Sale(models.Model):
    client = models.ForeignKey(Client, on_delete=models.DO_NOTHING)
    seller = models.ForeignKey(Seller, on_delete=models.DO_NOTHING)
    purchase_date = models.DateTimeField(null=False)
    is_paid = models.BooleanField(default=False)
    is_gathered = models.BooleanField(default=False)
    is_given = models.BooleanField(default=False)

    def __str__(self):
        return f'Продажа {self.id}'

class SoldProduct(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.DO_NOTHING)
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
    quantity = models.IntegerField(null=False, default=0)

    def __str__(self):
        return f'{self.quantity} товара {self.product.name} было продано в продаже № {self.sale.id}'
    
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Корзина клиента {self.user.first_name} (ID: {self.id})"

    def get_total_price(self):
         return sum(item.get_total_price() for item in self.items.all())
    
    def get_cart_items_count(self):
        return self.items.count()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.DO_NOTHING, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} (ID корзины: {self.cart.id})"

    def get_total_price(self):
        return self.product.price * self.quantity


class Material(models.Model):
    name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    current_quantity = models.IntegerField()

    def __str__(self):
        return self.name

class Supply(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.DO_NOTHING)
    supply_date = models.DateTimeField(null=False)

    def __str__(self):
        return f'Поставка {self.id}'

class SuppliedMaterial(models.Model):
    supply = models.ForeignKey(Supply, on_delete=models.DO_NOTHING, related_name="supplied_materials")
    material = models.ForeignKey(Material, on_delete=models.DO_NOTHING)
    quantity = models.IntegerField(null=False, default=0)

    def __str__(self):
         return f'{self.quantity} сырья {self.material.name} была добавлена в поставке {self.supply.id}'


class Service(models.Model):
    photo = models.ImageField(upload_to="images/services", default="images/no_photo.png")
    name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    duration = models.IntegerField(default=60)
    is_main = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def get_photo_url(self):
        if self.photo:
            return f"{settings.STATIC_URL}{self.photo}"
        return f"{settings.STATIC_URL}images/services/no_photo.png"

class Workshop(models.Model):
    photo = models.ImageField(upload_to="images/workshops", default="images/no_photo.png")
    name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    capacity = models.IntegerField()
    area = models.DecimalField(max_digits=10, decimal_places=1)

    def __str__(self):
        return self.name
    
    def get_photo_url(self):
        if self.photo:
            return f"{settings.STATIC_URL}{self.photo}"
        return f"{settings.STATIC_URL}images/workshops/no_photo.png"


class Appointment(models.Model):
    workshop = models.ForeignKey(Workshop, on_delete=models.DO_NOTHING)
    master = models.ForeignKey(Master, on_delete=models.DO_NOTHING, null=True, blank=True)
    client = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='client_appointments')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    main_service = models.ForeignKey(Service, on_delete=models.DO_NOTHING, related_name="main_appointments")
   
    def __str__(self):
        return f"Запись в мастерскую {self.workshop} клиента {self.client} к мастеру {self.master} в {self.start_time}"

class Order(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.DO_NOTHING)
    purchase_date = models.DateTimeField(null=False, auto_now_add=True)
    is_paid = models.BooleanField(default=False)
  
    def __str__(self):
       return f'Заказ {self.id}'
    def get_total_amount(self):
        main_service_price = self.appointment.main_service.price
        additional_services_price = self.orderadditionalservice_set.aggregate(
            total_price=models.Sum('service__price')
        )['total_price'] or 0
        return main_service_price + additional_services_price
    
class OrderAdditionalService(models.Model):
    order = models.ForeignKey(Order, on_delete=models.DO_NOTHING)
    service = models.ForeignKey(Service, on_delete=models.DO_NOTHING)

    class Meta:
        unique_together = ('order', 'service')
    def __str__(self):
        return f'Заказ {self.order.id} - основная услуга {self.service.name}'