import os
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.conf import settings
import json

from .models import Restaurant, Category, MenuItem, DiningTable, Order, OrderItem, PlatformSettings, GuestVisitor

# ==========================================
# 1. LANDING PAGE & TIZIM TANISHTIRUV
# ==========================================
def home_view(request):
    settings_obj, _ = PlatformSettings.objects.get_or_create(id=1)
    restaurants = Restaurant.objects.filter(is_active=True)[:9]
    total_restaurants = Restaurant.objects.filter(is_active=True).count()
    total_orders = Order.objects.count()
    total_dishes = MenuItem.objects.count()
    total_visitors = GuestVisitor.objects.count()
    return render(request, 'home.html', {
        'platform_settings': settings_obj,
        'restaurants': restaurants,
        'total_restaurants': total_restaurants,
        'total_orders': total_orders,
        'total_dishes': total_dishes,
        'total_visitors': total_visitors,
    })

# ==========================================
# 2. AUTENTIFIKATSIYA (LOGIN & REGISTER)
# ==========================================
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        restaurant_name = request.POST.get('restaurant_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Bu login band! Boshqa login tanlang.")
            return render(request, 'auth/register.html')
            
        user = User.objects.create_user(username=username, password=password)
        restaurant = Restaurant.objects.create(
            owner=user,
            name=restaurant_name,
            phone=phone,
            address=address
        )
        # Boshlang'ich default toifalarni ochib beramiz
        Category.objects.create(restaurant=restaurant, name="Taomlar", icon="utensils", order=1)
        Category.objects.create(restaurant=restaurant, name="Ichimliklar", icon="glass-whiskey", order=2)
        Category.objects.create(restaurant=restaurant, name="Salatlar", icon="carrot", order=3)
        
        # Boshlang'ich 5 ta stol yaratish
        for i in range(1, 6):
            DiningTable.objects.create(restaurant=restaurant, number=i, name=f"{i}-stol")
            
        login(request, user)
        messages.success(request, f"Xush kelibsiz! '{restaurant.name}' restorani yaratildi.")
        return redirect('dashboard')
        
    return render(request, 'auth/register.html')

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser and not hasattr(request.user, 'restaurant'):
            return redirect('super_dashboard')
        return redirect('dashboard')
        
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            # Agar superuser oddiy restoran loginidan kirsa ham xavfsiz o'z super paneliga o'tkaziladi
            login(request, user)
            if user.is_superuser and not hasattr(user, 'restaurant'):
                return redirect('super_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, "Login yoki parol noto'g'ri!")
            
    return render(request, 'auth/login.html')

# ==========================================
# SUPER ADMIN YAGONA PORTALI (/admin/)
# Agar login qilmagan bo'lsa -> Login ochiladi
# Agar login qilgan bo'lsa -> Super Admin Dashbordi ochiladi
# ==========================================
def admin_portal_view(request):
    # Agar tizimga kirgan bo'lsa
    if request.user.is_authenticated:
        # Rol tekshiruvi: faqat superuser bo'lsa
        if request.user.is_superuser:
            return super_dashboard_view(request)
        else:
            # Agar oddiy restoran egasi /admin/ ga kirsa, uni o'z restoraniga yo'naltirish
            messages.warning(request, "Siz Super Admin emassiz! Restoran kabinetingizga yo'naltirildingiz.")
            return redirect('dashboard')

    # Agar login qilmagan bo'lsa -> login formasini qabul qilish yoki ko'rsatish
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None and user.is_superuser:
            login(request, user)
            messages.success(request, "Super Admin tizimiga xush kelibsiz!")
            return redirect('admin_portal')
        else:
            messages.error(request, "Super Admin login yoki paroli xato!")
            
    return render(request, 'auth/super_login.html')

# ==========================================
# RESTORAN EGASI YAGONA PORTALI (/r/<slug>/dashboard/)
# Agar shu restoran egasi login qilmagan bo'lsa -> Restoranning o'z login sahifasi
# Agar login qilgan bo'lsa -> Restoranning shaxsiy dashbordi
# ==========================================
def restaurant_portal_view(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug)

    # Agar foydalanuvchi tizimga kirgan bo'lsa
    if request.user.is_authenticated:
        # Tekshiruv: bu user aynan shu restoranning egasimi?
        if hasattr(request.user, 'restaurant') and request.user.restaurant.id == restaurant.id:
            return dashboard_view(request)
        elif request.user.is_superuser:
            # Super admin istalgan restoranning kabinetini ko'ra oladi
            return dashboard_view(request)
        else:
            messages.error(request, f"Siz '{restaurant.name}' restoranining egasi emassiz!")
            return redirect('dashboard')

    # Agar login qilmagan bo'lsa -> shu restoranning login formasi
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            # Rol tekshiruvi: aynan shu restoranning egasi bo'lishi shart
            if hasattr(user, 'restaurant') and user.restaurant.id == restaurant.id:
                login(request, user)
                messages.success(request, f"'{restaurant.name}' kabinetiga xush kelibsiz!")
                return redirect('restaurant_portal', slug=slug)
            elif user.is_superuser:
                login(request, user)
                return redirect('admin_portal')
            else:
                messages.error(request, f"Ushbu login '{restaurant.name}' restoraniga tegishli emas!")
        else:
            messages.error(request, "Login yoki parol noto'g'ri!")

    return render(request, 'auth/restaurant_login.html', {'restaurant': restaurant})

def logout_view(request):
    logout(request)
    return redirect('home')

# ==========================================
# 3. SUPER ADMIN DASHBOARD (LOYIHA EGASI KABINETI)
# ==========================================
@login_required
def super_dashboard_view(request):
    if not request.user.is_superuser:
        messages.error(request, "Ushbu sahifaga faqat platforma asoschisi kira oladi!")
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        rest_id = request.POST.get('restaurant_id')
        restaurant = get_object_or_404(Restaurant, id=rest_id)
        
        if action == 'toggle_status':
            restaurant.is_active = not restaurant.is_active
            restaurant.save()
            status_text = "faollashtirildi" if restaurant.is_active else "bloklandi"
            messages.success(request, f"'{restaurant.name}' restorani {status_text}!")
        elif action == 'delete_restaurant':
            name = restaurant.name
            restaurant.owner.delete()
            messages.success(request, f"'{name}' restorani va uning barcha ma'lumotlari butunlay o'chirildi.")
            
        return redirect('admin_portal')

    all_restaurants = Restaurant.objects.all().order_by('-created_at')
    all_orders = Order.objects.all()
    total_income = all_orders.filter(status__in=['ACCEPTED', 'READY', 'COMPLETED']).aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_items = MenuItem.objects.count()
    recent_orders = all_orders.select_related('restaurant')[:15]
    
    # Storage kalkulyatsiyasi
    media_dir = settings.MEDIA_ROOT
    total_media_size = 0
    file_count = 0
    if os.path.exists(media_dir):
        for root, dirs, files in os.walk(media_dir):
            for f in files:
                fp = os.path.join(root, f)
                total_media_size += os.path.getsize(fp)
                file_count += 1
    total_media_mb = round(total_media_size / (1024 * 1024), 2)

    return render(request, 'dashboard/super_admin.html', {
        'restaurants': all_restaurants,
        'total_restaurants': all_restaurants.count(),
        'active_restaurants': all_restaurants.filter(is_active=True).count(),
        'total_orders': all_orders.count(),
        'total_income': total_income,
        'total_items': total_items,
        'recent_orders': recent_orders,
        'total_media_mb': total_media_mb,
        'file_count': file_count,
        'active_tab': 'overview'
    })

@login_required
def super_landing_settings_view(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    settings_obj, _ = PlatformSettings.objects.get_or_create(id=1)
    if request.method == 'POST':
        settings_obj.title = request.POST.get('title', settings_obj.title)
        settings_obj.tagline = request.POST.get('tagline', settings_obj.tagline)
        settings_obj.hero_title = request.POST.get('hero_title', settings_obj.hero_title)
        settings_obj.hero_description = request.POST.get('hero_description', settings_obj.hero_description)
        settings_obj.contact_phone = request.POST.get('contact_phone', settings_obj.contact_phone)
        settings_obj.contact_telegram = request.POST.get('contact_telegram', settings_obj.contact_telegram)
        settings_obj.announcement = request.POST.get('announcement', settings_obj.announcement)
        settings_obj.save()
        messages.success(request, "Landing page ma'lumotlari muvaffaqiyatli yangilandi!")
        return redirect('super_landing_settings')

    return render(request, 'dashboard/super_landing.html', {
        'settings_obj': settings_obj,
        'active_tab': 'landing'
    })

@login_required
def super_storage_view(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    media_dir = str(settings.MEDIA_ROOT)
    
    # Bazada amalda foydalanilayotgan barcha fayllar ro'yxatini yig'ish
    used_files = set()
    for r in Restaurant.objects.all():
        if r.logo:
            used_files.add(os.path.normpath(r.logo.name))
        if r.cover_image:
            used_files.add(os.path.normpath(r.cover_image.name))
            
    for item in MenuItem.objects.all():
        if item.image:
            used_files.add(os.path.normpath(item.image.name))
            
    for table in DiningTable.objects.all():
        if table.qr_code:
            used_files.add(os.path.normpath(table.qr_code.name))

    # O'chirish amali (Yagona fayl yoki barcha ortiqcha ishlatilmayotgan fayllarni o'chirish)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_file':
            rel_file = request.POST.get('file_path') # e.g. "menu_items/test.jpg"
            if rel_file:
                full_path = os.path.join(media_dir, rel_file)
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                        messages.success(request, f"'{os.path.basename(full_path)}' fayli serverdan muvaffaqiyatli o'chirildi!")
                    except Exception as e:
                        messages.error(request, f"O'chirishda xatolik: {e}")
        elif action == 'clean_all_unused':
            deleted_count = 0
            freed_bytes = 0
            if os.path.exists(media_dir):
                for root, dirs, files in os.walk(media_dir):
                    for f in files:
                        fp = os.path.join(root, f)
                        rel_path = os.path.normpath(os.path.relpath(fp, media_dir))
                        if rel_path not in used_files:
                            try:
                                sz = os.path.getsize(fp)
                                os.remove(fp)
                                deleted_count += 1
                                freed_bytes += sz
                            except Exception:
                                pass
            freed_kb = round(freed_bytes / 1024, 1)
            messages.success(request, f"Server tozalandi! {deleted_count} ta foydalanilmayotgan eskirgan rasm o'chirildi ({freed_kb} KB bo'shatildi).")
        return redirect('super_storage')

    files_list = []
    total_size = 0
    unused_count = 0
    unused_size = 0

    if os.path.exists(media_dir):
        for root, dirs, files in os.walk(media_dir):
            for f in files:
                fp = os.path.join(root, f)
                size_bytes = os.path.getsize(fp)
                total_size += size_bytes
                rel_path = os.path.normpath(os.path.relpath(fp, media_dir))
                is_used = rel_path in used_files
                
                if not is_used:
                    unused_count += 1
                    unused_size += size_bytes

                web_path = f"{settings.MEDIA_URL}{rel_path.replace(os.sep, '/')}"
                files_list.append({
                    'name': f,
                    'rel_path': rel_path.replace('\\', '/'),
                    'path': web_path,
                    'size_kb': round(size_bytes / 1024, 1),
                    'folder': os.path.basename(root) or 'media',
                    'is_used': is_used,
                })

    files_list.sort(key=lambda x: (x['is_used'], -x['size_kb']))
    total_mb = round(total_size / (1024 * 1024), 2)
    unused_kb = round(unused_size / 1024, 1)
    storage_limit_mb = 1000
    storage_percentage = round((total_mb / storage_limit_mb) * 100, 1)

    return render(request, 'dashboard/super_storage.html', {
        'files': files_list,
        'total_mb': total_mb,
        'storage_limit_mb': storage_limit_mb,
        'storage_percentage': storage_percentage,
        'file_count': len(files_list),
        'unused_count': unused_count,
        'unused_kb': unused_kb,
        'active_tab': 'storage'
    })

@login_required
def super_restaurants_view(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        rest_id = request.POST.get('restaurant_id')
        restaurant = get_object_or_404(Restaurant, id=rest_id)
        if action == 'toggle_status':
            restaurant.is_active = not restaurant.is_active
            restaurant.save()
            messages.success(request, f"'{restaurant.name}' statusi o'zgartirildi!")
        elif action == 'delete_restaurant':
            name = restaurant.name
            restaurant.owner.delete()
            messages.success(request, f"'{name}' o'chirildi.")
        return redirect('super_restaurants')

    restaurants = Restaurant.objects.all().order_by('-created_at')
    return render(request, 'dashboard/super_restaurants.html', {
        'restaurants': restaurants,
        'active_tab': 'restaurants'
    })

@login_required
def super_orders_view(request):
    if not request.user.is_superuser:
        return redirect('dashboard')

    orders = Order.objects.all().select_related('restaurant').prefetch_related('items').order_by('-created_at')
    return render(request, 'dashboard/super_orders.html', {
        'orders': orders,
        'active_tab': 'orders'
    })

# ==========================================
# 4. RESTORAN EGASI KABINETI (CLIENT DASHBOARD)
# ==========================================
@login_required
def dashboard_view(request):
    # Agar Superuser bo'lsa uni o'z maxfiy super paneliga yo'naltirish
    if request.user.is_superuser and not hasattr(request.user, 'restaurant'):
        return redirect('super_dashboard')
        
    # Restoran egasini tekshirish
    try:
        restaurant = request.user.restaurant
    except Restaurant.DoesNotExist:
        messages.error(request, "Sizda ulangan restoran mavjud emas!")
        return redirect('home')

    orders = Order.objects.filter(restaurant=restaurant)
    total_sales = orders.filter(status__in=['ACCEPTED', 'READY', 'COMPLETED']).aggregate(Sum('total_price'))['total_price__sum'] or 0
    today_orders = orders.filter(created_at__date=timezone.now().date())
    today_sales = today_orders.filter(status__in=['ACCEPTED', 'READY', 'COMPLETED']).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    pending_count = orders.filter(status='PENDING').count()
    preparing_count = orders.filter(status='ACCEPTED').count()
    
    recent_orders = orders[:10]
    menu_count = MenuItem.objects.filter(restaurant=restaurant).count()
    table_count = DiningTable.objects.filter(restaurant=restaurant).count()

    context = {
        'restaurant': restaurant,
        'total_sales': total_sales,
        'today_sales': today_sales,
        'total_orders_count': orders.count(),
        'today_orders_count': today_orders.count(),
        'pending_count': pending_count,
        'preparing_count': preparing_count,
        'menu_count': menu_count,
        'table_count': table_count,
        'recent_orders': recent_orders,
    }
    return render(request, 'dashboard/index.html', context)

# ==========================================
# 4. KABINET: MENYU TAOMLAR VA KATEGORIYALAR BOSHQARUVI
# ==========================================
@login_required
def menu_items_view(request):
    restaurant = request.user.restaurant
    categories = Category.objects.filter(restaurant=restaurant)
    items = MenuItem.objects.filter(restaurant=restaurant).select_related('category').order_by('-id')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_category':
            cat_name = request.POST.get('name')
            icon = request.POST.get('icon', 'utensils')
            if cat_name:
                Category.objects.create(restaurant=restaurant, name=cat_name, icon=icon)
                messages.success(request, f"'{cat_name}' toifasi qo'shildi!")
                
        elif action == 'add_item':
            cat_id = request.POST.get('category_id')
            name = request.POST.get('name')
            price = request.POST.get('price')
            description = request.POST.get('description', '')
            image = request.FILES.get('image')
            
            category = get_object_or_404(Category, id=cat_id, restaurant=restaurant)
            MenuItem.objects.create(
                restaurant=restaurant,
                category=category,
                name=name,
                price=price,
                description=description,
                image=image,
                is_available=True
            )
            messages.success(request, f"'{name}' taomi menyuga qo'shildi!")
            
        elif action == 'edit_item':
            item_id = request.POST.get('item_id')
            item = get_object_or_404(MenuItem, id=item_id, restaurant=restaurant)
            cat_id = request.POST.get('category_id')
            item.name = request.POST.get('name', item.name)
            item.price = request.POST.get('price', item.price)
            item.description = request.POST.get('description', item.description)
            if cat_id:
                category = get_object_or_404(Category, id=cat_id, restaurant=restaurant)
                item.category = category
            if request.FILES.get('image'):
                item.image = request.FILES.get('image')
            item.save()
            messages.success(request, f"'{item.name}' taomi muvaffaqiyatli tahrirlandi!")

        elif action == 'toggle_availability':
            item_id = request.POST.get('item_id')
            item = get_object_or_404(MenuItem, id=item_id, restaurant=restaurant)
            item.is_available = not item.is_available
            item.save()
            return JsonResponse({'status': 'ok', 'is_available': item.is_available})

        elif action == 'delete_item':
            item_id = request.POST.get('item_id')
            item = get_object_or_404(MenuItem, id=item_id, restaurant=restaurant)
            item.delete()
            messages.success(request, "Taom o'chirildi.")
            
        return redirect('menu_items')

    return render(request, 'dashboard/menu_items.html', {
        'restaurant': restaurant,
        'categories': categories,
        'items': items,
    })

# ==========================================
# 5. KABINET: STOLLAR VA QR KODLAR
# ==========================================
@login_required
def tables_view(request):
    restaurant = request.user.restaurant
    tables = DiningTable.objects.filter(restaurant=restaurant).order_by('number')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_table':
            number = request.POST.get('number')
            name = request.POST.get('name', 'Stol')
            try:
                table = DiningTable.objects.create(
                    restaurant=restaurant,
                    number=number,
                    name=name
                )
                # QR kod hosil qilish
                menu_url = request.build_absolute_uri(f"/r/{restaurant.slug}/?table={table.number}")
                qr = qrcode.QRCode(version=1, box_size=8, border=2)
                qr.add_data(menu_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                table.qr_code.save(f"qr_{restaurant.slug}_table_{table.number}.png", ContentFile(buffer.getvalue()))
                table.save()
                messages.success(request, f"{number}-stol va uning QR kodi yaratildi!")
            except Exception as e:
                messages.error(request, "Bunday raqamli stol allaqachon mavjud!")
                
        elif action == 'delete_table':
            t_id = request.POST.get('table_id')
            table = get_object_or_404(DiningTable, id=t_id, restaurant=restaurant)
            table.delete()
            messages.success(request, "Stol o'chirildi.")
            
        return redirect('tables')

    return render(request, 'dashboard/tables.html', {
        'restaurant': restaurant,
        'tables': tables,
    })

# Stollar QR kodlarini chop etish (barchasini bitta sahifada yoki alohida)
@login_required
def print_all_tables_qr(request):
    restaurant = request.user.restaurant
    tables = DiningTable.objects.filter(restaurant=restaurant).order_by('number')
    
    # Har bir stolda QR kod mavjudligini ta'minlash
    for table in tables:
        if not table.qr_code:
            menu_url = request.build_absolute_uri(f"/r/{restaurant.slug}/?table={table.number}")
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(menu_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            table.qr_code.save(f"qr_{restaurant.slug}_table_{table.number}.png", ContentFile(buffer.getvalue()))
            table.save()

    return render(request, 'dashboard/print_qr_all.html', {
        'restaurant': restaurant,
        'tables': tables,
    })

@login_required
def print_single_table_qr(request, table_id):
    restaurant = request.user.restaurant
    table = get_object_or_404(DiningTable, id=table_id, restaurant=restaurant)
    
    if not table.qr_code:
        menu_url = request.build_absolute_uri(f"/r/{restaurant.slug}/?table={table.number}")
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(menu_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        table.qr_code.save(f"qr_{restaurant.slug}_table_{table.number}.png", ContentFile(buffer.getvalue()))
        table.save()

    return render(request, 'dashboard/print_qr_all.html', {
        'restaurant': restaurant,
        'tables': [table],
        'is_single': True
    })

# ==========================================
# 6. KABINET: RESTORAN PROFIL VA SOZLAMALARI
# ==========================================
# ==========================================
# 6. KABINET: RESTORAN PROFIL VA SOZLAMALARI
# ==========================================
@login_required
def settings_view(request):
    restaurant = request.user.restaurant
    if request.method == 'POST':
        restaurant.name = request.POST.get('name', restaurant.name)
        restaurant.description = request.POST.get('description', restaurant.description)
        restaurant.phone = request.POST.get('phone', restaurant.phone)
        restaurant.address = request.POST.get('address', restaurant.address)
        restaurant.wifi_name = request.POST.get('wifi_name', restaurant.wifi_name)
        restaurant.wifi_pass = request.POST.get('wifi_pass', restaurant.wifi_pass)
        restaurant.instagram = request.POST.get('instagram', restaurant.instagram)
        restaurant.telegram = request.POST.get('telegram', restaurant.telegram)
        
        if request.FILES.get('logo'):
            restaurant.logo = request.FILES.get('logo')
        if request.FILES.get('cover_image'):
            restaurant.cover_image = request.FILES.get('cover_image')
        if request.FILES.get('about_cover'):
            restaurant.about_cover = request.FILES.get('about_cover')
            
        restaurant.save()
        messages.success(request, "Restoran sozlamalari yangilandi!")
        return redirect('settings')
        
    return render(request, 'dashboard/settings.html', {'restaurant': restaurant})

# ==========================================
# 7. OSHXONA KABINETI (KDS - KITCHEN DISPLAY SYSTEM) REAL-VAQT
# ==========================================
@login_required
def kitchen_view(request):
    restaurant = request.user.restaurant
    return render(request, 'dashboard/kitchen.html', {'restaurant': restaurant})

# Oshxona API: Yangi buyurtmalarni olish (Har 3 soniyada polling orqali jonli yangilanadi)
@login_required
def api_kitchen_orders(request):
    restaurant = request.user.restaurant
    active_orders = Order.objects.filter(
        restaurant=restaurant,
        status__in=['PENDING', 'ACCEPTED', 'READY']
    ).prefetch_related('items').order_by('created_at')

    data = []
    for o in active_orders:
        items = [{'name': i.item_name, 'quantity': i.quantity, 'price': float(i.price), 'total': float(i.total)} for i in o.items.all()]
        data.append({
            'id': o.id,
            'table_number': o.table_number,
            'status': o.status,
            'status_display': o.get_status_display(),
            'total_price': float(o.total_price),
            'customer_notes': o.customer_notes or '',
            'estimated_minutes': o.estimated_minutes,
            'ready_timestamp': o.ready_timestamp,
            'created_at': o.created_at.strftime("%H:%M"),
            'items': items,
        })
    return JsonResponse({'orders': data})

# Oshxona API: Buyurtmani qabul qilish va vaqt belgilash
@csrf_exempt
@login_required
def api_kitchen_update_order(request, order_id):
    restaurant = request.user.restaurant
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            action = body.get('action') # 'accept', 'ready', 'complete', 'cancel'
            
            if action == 'accept':
                mins = int(body.get('minutes', 15))
                order.status = 'ACCEPTED'
                order.estimated_minutes = mins
                order.accepted_at = timezone.now()
                order.save()
            elif action == 'ready':
                order.status = 'READY'
                order.ready_at = timezone.now()
                order.save()
            elif action == 'complete':
                # Oshxona "Yetkazildi" qilganda avtomatik KASSAGA (DELIVERED) o'tadi
                order.status = 'DELIVERED'
                order.delivered_at = timezone.now()
                order.save()
            elif action == 'cancel':
                reason = body.get('reason', 'Oshxonada mahsulot yetishmadi yoki bekor qilindi')
                by_who = body.get('cancelled_by', 'KITCHEN')
                order.status = 'CANCELLED'
                order.cancelled_by = by_who
                order.cancellation_reason = reason
                order.save()
                
            return JsonResponse({'status': 'ok', 'order_status': order.status})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'method not allowed'}, status=405)


# ==========================================
# 7.5. KASSA VA TO'LOVLAR BOSHQARUVI (/dashboard/cashier/)
# ==========================================
@login_required
def cashier_view(request):
    restaurant = request.user.restaurant
    today = timezone.now().date()
    pending_orders = Order.objects.filter(restaurant=restaurant, status='DELIVERED', is_paid=False)
    pending_count = pending_orders.count()
    pending_revenue = pending_orders.aggregate(s=Sum('total_price'))['s'] or 0
    today_revenue = Order.objects.filter(restaurant=restaurant, status='COMPLETED', is_paid=True, paid_at__date=today).aggregate(s=Sum('total_price'))['s'] or 0
    return render(request, 'dashboard/cashier.html', {
        'restaurant': restaurant,
        'pending_count': pending_count,
        'pending_revenue': pending_revenue,
        'today_revenue': today_revenue
    })


# Kassa API: Yetkazilgan (to'lov kutilayotgan) buyurtmalarni olish va kunlik statistika
@login_required
def api_cashier_orders(request):
    restaurant = request.user.restaurant
    today = timezone.now().date()
    
    # 1. Kassada to'lov kutilayotganlar
    orders = Order.objects.filter(
        restaurant=restaurant,
        status='DELIVERED',
        is_paid=False
    ).select_related('guest_visitor').prefetch_related('items').order_by('-delivered_at', '-created_at')

    # 2. Bugungi to'langan tushum
    today_paid_orders = Order.objects.filter(
        restaurant=restaurant,
        status='COMPLETED',
        is_paid=True,
        paid_at__date=today
    )
    today_revenue = today_paid_orders.aggregate(s=Sum('total_price'))['s'] or 0
    today_paid_count = today_paid_orders.count()

    # 3. Kutilayotgan to'lovlar summasi
    pending_revenue = orders.aggregate(s=Sum('total_price'))['s'] or 0

    data = []
    for o in orders:
        items = [{'name': i.item_name, 'quantity': i.quantity, 'price': float(i.price), 'total': float(i.total)} for i in o.items.all()]
        data.append({
            'id': o.id,
            'table_number': o.table_number,
            'status': o.status,
            'status_display': o.get_status_display(),
            'total_price': float(o.total_price),
            'customer_notes': o.customer_notes or '',
            'created_at': o.created_at.strftime("%H:%M"),
            'delivered_at': o.delivered_at.strftime("%H:%M") if o.delivered_at else "",
            'client_name': o.guest_visitor.client_name if o.guest_visitor and o.guest_visitor.client_name else '',
            'client_phone': o.guest_visitor.client_phone if o.guest_visitor and o.guest_visitor.client_phone else '',
            'items': items,
        })
    return JsonResponse({
        'orders': data,
        'today_revenue': float(today_revenue),
        'today_paid_count': today_paid_count,
        'pending_revenue': float(pending_revenue),
        'pending_count': orders.count(),
    })


# Realtime Sidebar Badge Counts API (Kassa va Oshxona badge larini barcha sahifalarda yangilash)
@login_required
def api_sidebar_badge_counts(request):
    restaurant = request.user.restaurant
    pending_kitchen = Order.objects.filter(restaurant=restaurant, status='PENDING').count()
    pending_cashier = Order.objects.filter(restaurant=restaurant, status='DELIVERED', is_paid=False).count()
    return JsonResponse({
        'kitchen_count': pending_kitchen,
        'cashier_count': pending_cashier
    })



# Kassa API: To'lovni qabul qilish va Yakunlash (Tarixga o'tkazish)
@csrf_exempt
@login_required
def api_cashier_pay_order(request, order_id):
    restaurant = request.user.restaurant
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            method = body.get('payment_method', 'CASH')
            
            order.status = 'COMPLETED'
            order.is_paid = True
            order.payment_method = method
            order.paid_at = timezone.now()
            order.save()

            return JsonResponse({'status': 'ok', 'message': "To'lov muvaffaqiyatli qabul qilindi va buyurtma tarixga o'tkazildi!"})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'method not allowed'}, status=405)



# ==========================================
# 8. RESTORAN BUYURTMA TARIXI VA ANALITIKA (/dashboard/history/)
# ==========================================
@login_required
def history_view(request):
    restaurant = request.user.restaurant
    orders = Order.objects.filter(restaurant=restaurant).prefetch_related('items').order_by('-created_at')
    
    # Filterlar
    date_filter = request.GET.get('date', '')
    table_filter = request.GET.get('table', '')
    status_filter = request.GET.get('status', '')

    if date_filter:
        orders = orders.filter(created_at__date=date_filter)
        
    if table_filter and table_filter.isdigit():
        orders = orders.filter(table_number=int(table_filter))

    if status_filter:
        orders = orders.filter(status=status_filter)

    # Statistika tahlili (Filterlangan buyurtmalar bo'yicha)
    total_count = orders.count()
    completed_orders = orders.filter(status='COMPLETED')
    cancelled_orders = orders.filter(status='CANCELLED')
    total_revenue = completed_orders.aggregate(s=Sum('total_price'))['s'] or 0
    cancelled_revenue = cancelled_orders.aggregate(s=Sum('total_price'))['s'] or 0

    # Mavjud stollar
    all_tables = DiningTable.objects.filter(restaurant=restaurant).order_by('number')

    # Agar ma'lum bir stol va sana tanlansa, o'sha stol sessiyasi tahlili
    table_session_stats = None
    if table_filter and table_filter.isdigit():
        tbl_num = int(table_filter)
        tbl_orders = orders.filter(table_number=tbl_num)
        
        # O'sha stoldagi mehmonlar (GuestVisitor)
        table_visitors = GuestVisitor.objects.filter(restaurant=restaurant, table_number=tbl_num)
        if date_filter:
            table_visitors = table_visitors.filter(last_seen__date=date_filter)

        table_session_stats = {
            'table_number': tbl_num,
            'orders_count': tbl_orders.count(),
            'total_spent': tbl_orders.filter(status='COMPLETED').aggregate(s=Sum('total_price'))['s'] or 0,
            'visitors_count': table_visitors.count(),
            'active_visitors': table_visitors.filter(is_active=True).count(),
            'visitors': table_visitors[:10],
        }

    return render(request, 'dashboard/history.html', {
        'restaurant': restaurant,
        'orders': orders[:150], # pagination / limit
        'total_count': total_count,
        'total_revenue': total_revenue,
        'cancelled_count': cancelled_orders.count(),
        'cancelled_revenue': cancelled_revenue,
        'all_tables': all_tables,
        'selected_date': date_filter,
        'selected_table': table_filter,
        'selected_status': status_filter,
        'table_session_stats': table_session_stats,
    })


# ==========================================
# 9. RESTORAN MEHMONLARI (USERLAR / DEVICES) (/dashboard/visitors/)
# ==========================================
@login_required
def visitors_view(request):
    restaurant = request.user.restaurant
    visitors = GuestVisitor.objects.filter(restaurant=restaurant).order_by('-last_seen')

    # Filterlar
    status_filter = request.GET.get('status', '')
    table_filter = request.GET.get('table', '')
    search_query = request.GET.get('q', '')

    if status_filter == 'active':
        visitors = visitors.filter(is_active=True)
    elif status_filter == 'inactive':
        visitors = visitors.filter(is_active=False)

    if table_filter and table_filter.isdigit():
        visitors = visitors.filter(table_number=int(table_filter))

    if search_query:
        visitors = visitors.filter(
            Q(client_name__icontains=search_query) |
            Q(client_phone__icontains=search_query) |
            Q(device_name__icontains=search_query) |
            Q(os_name__icontains=search_query) |
            Q(guest_uuid__icontains=search_query) |
            Q(ip_address__icontains=search_query)
        )

    total_visitors = GuestVisitor.objects.filter(restaurant=restaurant).count()
    active_visitors = GuestVisitor.objects.filter(restaurant=restaurant, is_active=True).count()
    inactive_visitors = total_visitors - active_visitors
    all_tables = DiningTable.objects.filter(restaurant=restaurant).order_by('number')

    return render(request, 'dashboard/visitors.html', {
        'restaurant': restaurant,
        'visitors': visitors[:150],
        'total_visitors': total_visitors,
        'active_visitors': active_visitors,
        'inactive_visitors': inactive_visitors,
        'all_tables': all_tables,
        'selected_status': status_filter,
        'selected_table': table_filter,
        'search_query': search_query,
    })


# ==========================================
# 10. MIJOZLAR MENYUSI (MOBIL ILOVADEK INTERFEYS)
# ==========================================
def public_menu_view(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    table_number = request.GET.get('table', '1')
    categories = Category.objects.filter(restaurant=restaurant).prefetch_related('items')
    
    return render(request, 'client/mobile_menu.html', {
        'restaurant': restaurant,
        'table_number': table_number,
        'categories': categories,
    })

# Qurilma va Mehmonni ro'yxatga olish / Track qilish API
@csrf_exempt
def api_track_visitor(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            guest_uuid = data.get('guest_uuid')
            table_number = int(data.get('table_number', 1))
            device_name = data.get('device_name', "Noma'lum Qurilma")
            os_name = data.get('os_name', "Noma'lum OS")
            browser_name = data.get('browser_name', "Noma'lum Brauzer")
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip()

            client_name = data.get('client_name', '').strip()
            client_phone = data.get('client_phone', '').strip()

            if not guest_uuid:
                return JsonResponse({'status': 'error', 'message': 'UUID kerak'}, status=400)

            visitor, created = GuestVisitor.objects.get_or_create(
                restaurant=restaurant,
                guest_uuid=guest_uuid,
                defaults={
                    'table_number': table_number,
                    'client_name': client_name if client_name else None,
                    'client_phone': client_phone if client_phone else None,
                    'device_name': device_name,
                    'os_name': os_name,
                    'browser_name': browser_name,
                    'user_agent': user_agent,
                    'ip_address': ip_address,
                }
            )

            if not created:
                visitor.table_number = table_number
                if client_name:
                    visitor.client_name = client_name
                if client_phone:
                    visitor.client_phone = client_phone
                visitor.device_name = device_name
                visitor.os_name = os_name
                visitor.browser_name = browser_name
                visitor.user_agent = user_agent
                visitor.ip_address = ip_address
                visitor.last_seen = timezone.now()
                visitor.save()

            # Mehmonning oldingi buyurtmalarini olish
            orders = Order.objects.filter(restaurant=restaurant, guest_uuid=guest_uuid).order_by('-created_at')[:10]
            orders_data = [{
                'id': o.id,
                'table_number': o.table_number,
                'status': o.status,
                'status_display': o.get_status_display(),
                'total_price': float(o.total_price),
                'created_at': o.created_at.strftime("%d.%m.%Y %H:%M"),
                'items_count': o.items.count(),
                'items': [{'name': i.item_name, 'quantity': i.quantity, 'price': float(i.price)} for i in o.items.all()]
            } for o in orders]

            return JsonResponse({
                'status': 'ok',
                'guest_uuid': visitor.guest_uuid,
                'client_name': visitor.client_name or '',
                'client_phone': visitor.client_phone or '',
                'is_active': visitor.is_active,
                'orders': orders_data
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'method not allowed'}, status=405)

# Mijoz buyurtma berish API
@csrf_exempt
def api_create_order(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            table_number = int(data.get('table_number', 1))
            items_data = data.get('items', [])
            customer_notes = data.get('notes', '')
            guest_uuid = data.get('guest_uuid', '')

            if not items_data:
                return JsonResponse({'status': 'error', 'message': "Savat bo'sh!"}, status=400)

            # Mehmonni topish va aktivlashtirish
            guest_visitor = None
            if guest_uuid:
                guest_visitor = GuestVisitor.objects.filter(restaurant=restaurant, guest_uuid=guest_uuid).first()
                if guest_visitor:
                    guest_visitor.is_active = True
                    guest_visitor.table_number = table_number
                    guest_visitor.save()

            total_sum = 0
            order = Order.objects.create(
                restaurant=restaurant,
                table_number=table_number,
                customer_notes=customer_notes,
                guest_visitor=guest_visitor,
                guest_uuid=guest_uuid,
                status='PENDING'
            )

            for itm in items_data:
                item_id = itm.get('id')
                qty = int(itm.get('quantity', 1))
                menu_item = get_object_or_404(MenuItem, id=item_id, restaurant=restaurant)
                
                subtotal = menu_item.price * qty
                total_sum += subtotal
                
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    item_name=menu_item.name,
                    price=menu_item.price,
                    quantity=qty
                )

            order.total_price = total_sum
            order.save()

            return JsonResponse({
                'status': 'ok',
                'order_id': order.id,
                'message': "Buyurtma oshxonaga yetkazildi!"
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'method not allowed'}, status=405)

# Mijoz status tekshirish API (Teskari sanoq va jonli holat)
def api_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return JsonResponse({
        'id': order.id,
        'status': order.status,
        'status_display': order.get_status_display(),
        'table_number': order.table_number,
        'total_price': float(order.total_price),
        'estimated_minutes': order.estimated_minutes,
        'accepted_at': order.accepted_at.isoformat() if order.accepted_at else None,
        'ready_timestamp': order.ready_timestamp,
        'cancelled_by': order.get_cancelled_by_display() if order.cancelled_by else None,
        'cancellation_reason': order.cancellation_reason or '',
        'items': [{'name': i.item_name, 'quantity': i.quantity, 'price': float(i.price)} for i in order.items.all()]
    })
