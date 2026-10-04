# Girgitdon - Restoran va Kafe Menyu hamda Boshqaruv Tizimi

Zamonaviy QR menyu, oshxona buyurtmalari (KDS) va kassa boshqaruvi tizimi.

## Imkoniyatlari
- **QR Menyu:** Mijozlar o'z stolidan menyuni ko'rish, taom tanlash va buyurtma berish imkoniyati.
- **Oshxona (KDS):** Yangi tushgan buyurtmalarni real vaqt rejimida qabul qilish, tayyorlash va yetkazish.
- **Kassa & To'lovlar:** Oshxonadan yetkazilgan stollarni hisob-kitob qilish, to'lov turlari (Naqd, Karta, Payme/Click) va audio bildirishnomalar.
- **Super Admin va Restoran Sozlamalari:** Stollar, toifalar, taomlar va restoran profilini to'liq boshqarish.

## Ishga tushirish
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```
