import os
import django
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from menu.models import Restaurant, Category, MenuItem, DiningTable, Order, OrderItem

def seed_data():
    print("Boshlang'ich ma'lumotlar kiritilmoqda...")
    
    # 1. Superuser
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Superuser: login: admin, parol: admin123")
        
    # 2. Demo Restoran Egasi
    owner_user, _ = User.objects.get_or_create(username='safari_admin')
    owner_user.set_password('12345')
    owner_user.save()
    
    # Restoran
    restaurant, created = Restaurant.objects.get_or_create(
        owner=owner_user,
        defaults={
            'name': 'Safari Lounge & Cafe',
            'phone': '+998 90 999 88 77',
            'address': 'Toshkent sh., Amir Temur shox ko\'chasi 15',
            'description': 'Mazali milliy va yevropa taomlari, shinam muhit va tezkor xizmat!',
            'wifi_name': 'Safari_Guest',
            'wifi_pass': 'safari2026'
        }
    )
    
    # Kategoriyalar
    cat_fastfood, _ = Category.objects.get_or_create(restaurant=restaurant, name="Fast Food & Burgerlar", icon="burger", order=1)
    cat_hot, _ = Category.objects.get_or_create(restaurant=restaurant, name="Issiq Taomlar", icon="utensils", order=2)
    cat_drinks, _ = Category.objects.get_or_create(restaurant=restaurant, name="Ichimliklar & Kofe", icon="mug-hot", order=3)
    cat_salads, _ = Category.objects.get_or_create(restaurant=restaurant, name="Salatlar", icon="carrot", order=4)

    # Taomlar
    items = [
        {"cat": cat_fastfood, "name": "Klassik Chizburger", "price": 42000, "desc": "100% mol go'shti kotleti, erigan cheddr pishlog'i, marinadlangan bodring va maxsus sous."},
        {"cat": cat_fastfood, "name": "Go'shtli Lavash Big", "price": 38000, "desc": "Tandir go'shti, pomidor, bodring, chipslar va oshpaz sousi."},
        {"cat": cat_hot, "name": "To'y Oshi (Choyxona palov)", "price": 45000, "desc": "Lazer guruch, mayin lahm go'sht, noxat, mayiz va bedana tuxumi bilan."},
        {"cat": cat_hot, "name": "Mol Go'shtli Qozon Kabob", "price": 68000, "desc": "Qarsildoq kartoshka va marinadlangan suvli go'sht bo'laklari."},
        {"cat": cat_salads, "name": "Sezar Salati (Tovuqli)", "price": 35000, "desc": "Grilda pishgan tovuq filesi, aysberg barglari, parmezan va suxariklar."},
        {"cat": cat_drinks, "name": "Kapuchino Kofe", "price": 22000, "desc": "Yangi tuyilgan qahva donalaridan quyuq sut ko'pigi bilan."},
        {"cat": cat_drinks, "name": "Yalpizli Limonad (1 litr)", "price": 28000, "desc": "Yangi siqilgan limon sharbati, muz va xushbo'y yalpiz barglari."},
    ]

    for itm in items:
        MenuItem.objects.get_or_create(
            restaurant=restaurant,
            name=itm["name"],
            defaults={
                "category": itm["cat"],
                "price": itm["price"],
                "description": itm["desc"],
                "is_available": True
            }
        )

    # Stollar va QR Kodlar
    for t_num in range(1, 7):
        table, t_created = DiningTable.objects.get_or_create(
            restaurant=restaurant,
            number=t_num,
            defaults={'name': f"Stol"}
        )
        if not table.qr_code:
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(f"http://127.0.0.1:8000/r/{restaurant.slug}/?table={table.number}")
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buf = BytesIO()
            img.save(buf, format='PNG')
            table.qr_code.save(f"qr_{restaurant.slug}_table_{t_num}.png", ContentFile(buf.getvalue()))
            table.save()

    print("Muvaffaqiyatli yakunlandi!")

if __name__ == '__main__':
    seed_data()
