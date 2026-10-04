import os
import django
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from menu.models import DiningTable

def update_qrs(ip):
    tables = DiningTable.objects.all()
    for table in tables:
        menu_url = f"http://{ip}:8000/r/{table.restaurant.slug}/?table={table.number}"
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(menu_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = BytesIO()
        img.save(buf, format='PNG')
        table.qr_code.save(f"qr_{table.restaurant.slug}_table_{table.number}.png", ContentFile(buf.getvalue()), save=True)
        print(f"Updated table {table.number} QR: {menu_url}")

if __name__ == '__main__':
    update_qrs("192.168.1.198")
