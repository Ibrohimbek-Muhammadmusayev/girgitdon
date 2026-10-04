from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
import os

class Restaurant(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='restaurant')
    name = models.CharField(max_length=200, verbose_name="Restoran nomi")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, null=True, verbose_name="Restoran haqida")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Logotip")
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True, verbose_name="Menyu tepasi Banner rasmi")
    about_cover = models.ImageField(upload_to='covers/', blank=True, null=True, verbose_name="Restoran Haqida (Tashqi ko'rinish) Banneri")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Telefon")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Manzil")
    wifi_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Wi-Fi nomi")
    wifi_pass = models.CharField(max_length=100, blank=True, null=True, verbose_name="Wi-Fi paroli")
    instagram = models.CharField(max_length=150, blank=True, null=True, verbose_name="Instagram linki yoki username")
    telegram = models.CharField(max_length=150, blank=True, null=True, verbose_name="Telegram linki yoki username")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            count = 1
            while Restaurant.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100, verbose_name="Toifa nomi")
    icon = models.CharField(max_length=50, default='utensils', help_text="FontAwesome yoki emoji belgisi")
    order = models.IntegerField(default=0, verbose_name="Tartib raqami")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"

class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200, verbose_name="Taom nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Tarkibi va tavsifi")
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Narxi (so'm)")
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True, verbose_name="Taom rasmi")
    is_available = models.BooleanField(default=True, verbose_name="Mavjudmi (sotuvda bormi)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class DiningTable(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    number = models.IntegerField(verbose_name="Stol raqami")
    name = models.CharField(max_length=50, default="Stol", verbose_name="Nomi / Turi")
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)

    class Meta:
        unique_together = ('restaurant', 'number')

    def __str__(self):
        return f"{self.restaurant.name} - {self.name} #{self.number}"

class GuestVisitor(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='visitors')
    guest_uuid = models.CharField(max_length=64, db_index=True, verbose_name="Mehmon Unique ID")
    table_number = models.IntegerField(null=True, blank=True, verbose_name="Oxirgi o'tirgan stoli")
    
    # Mehmon Shaxsiy Ma'lumotlari (Profil to'ldirgan bo'lsa)
    client_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="Mijoz Ismi")
    client_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Mijoz Telefoni")
    
    # Qurilma ma'lumotlari
    device_name = models.CharField(max_length=150, default="Noma'lum Qurilma", verbose_name="Qurilma rusumi")
    os_name = models.CharField(max_length=100, default="Noma'lum OS", verbose_name="Operatsion tizim")
    browser_name = models.CharField(max_length=100, default="Noma'lum Brauzer", verbose_name="Brauzer")
    user_agent = models.TextField(blank=True, null=True, verbose_name="User Agent")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Manzil")
    
    # Holat & Faollik
    is_active = models.BooleanField(default=False, verbose_name="Faolmi (Buyurtma berganmi)")
    first_seen = models.DateTimeField(auto_now_add=True, verbose_name="Birinchi kirish vaqti")
    last_seen = models.DateTimeField(auto_now=True, verbose_name="Oxirgi faollik vaqti")
    
    class Meta:
        ordering = ['-last_seen']
        unique_together = ('restaurant', 'guest_uuid')

    def __str__(self):
        status = "Faol (Buyurtma qilgan)" if self.is_active else "Nofaol (Faqat ko'rgan)"
        return f"{self.device_name} (Stol #{self.table_number or '?'}) - {status}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Kutilmoqda'),
        ('ACCEPTED', 'Qabul qilindi (Tayyorlanmoqda)'),
        ('READY', 'Tayyor'),
        ('DELIVERED', 'Yetkazildi (Kassada kutilmoqda)'),
        ('COMPLETED', 'To\'landi & Yakunlandi'),
        ('CANCELLED', 'Bekor qilindi'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Naqd pul'),
        ('CARD', 'Plastik karta (Humo/Uzcard)'),
        ('PAYME', 'Payme / Click / Online'),
        ('OTHER', 'Boshqa'),
    ]

    CANCELLED_BY_CHOICES = [
        ('KITCHEN', 'Oshxona (Oshpaz)'),
        ('STAFF', 'Admin / Ofitsiant'),
        ('CUSTOMER', 'Mijoz o\'zi'),
        ('SYSTEM', 'Tizim'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    guest_visitor = models.ForeignKey(GuestVisitor, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    guest_uuid = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    table = models.ForeignKey(DiningTable, on_delete=models.SET_NULL, null=True, blank=True)
    table_number = models.IntegerField(verbose_name="Stol raqami")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_price = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    customer_notes = models.TextField(blank=True, null=True, verbose_name="Mijoz izohi")
    
    # To'lov va Kassa ma'lumotlari
    is_paid = models.BooleanField(default=False, verbose_name="To'langanmi")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True, verbose_name="To'lov turi")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="To'langan vaqti")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Yetkazilgan vaqti")
    
    # Bekor qilinganlik ma'lumotlari
    cancelled_by = models.CharField(max_length=20, choices=CANCELLED_BY_CHOICES, blank=True, null=True, verbose_name="Kim bekor qildi")
    cancellation_reason = models.TextField(blank=True, null=True, verbose_name="Bekor qilish sababi")
    
    # Tayyorlanish vaqti
    estimated_minutes = models.IntegerField(default=15, verbose_name="Tayyorlanish vaqti (daqiqa)")
    accepted_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def ready_timestamp(self):
        """Mijoz ekranidagi teskari taymer uchun ISO formatda tayyor bo'lish vaqti"""
        if self.accepted_at and self.estimated_minutes:
            target = self.accepted_at + timezone.timedelta(minutes=self.estimated_minutes)
            return target.isoformat()
        return None

    def __str__(self):
        return f"Order #{self.id} - Stol {self.table_number} ({self.get_status_display()})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    item_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.item_name} x {self.quantity}"

class PlatformSettings(models.Model):
    title = models.CharField(max_length=200, default="Girgitdon", verbose_name="Platforma Nomi")
    tagline = models.CharField(max_length=255, default="Kafe va Restoranlar uchun Raqamli QR Menyu Platformasi", verbose_name="Qisqa shior")
    hero_title = models.CharField(max_length=255, default="Zamonaviy QR Menyu & Real-vaqt Oshxona Tizimi", verbose_name="Bosh sahifa asosiy sarlavha")
    hero_description = models.TextField(default="Mijozlar telefonida qulay mobil menyuni ko'radi va darhol stoldan buyurtma beradi. Oshxona esa buyurtmani qabul qilib, tayyorlanish vaqtini belgilaydi — mijozda teskari sanoq ishlaydi!", verbose_name="Bosh sahifa matni")
    contact_phone = models.CharField(max_length=50, blank=True, null=True, default="+998 90 000 00 00", verbose_name="Aloqa telefoni")
    contact_telegram = models.CharField(max_length=100, blank=True, null=True, default="girgitdon_admin", verbose_name="Telegram admin")
    announcement = models.TextField(blank=True, null=True, verbose_name="Bosh sahifadagi e'lon / yangilik")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
