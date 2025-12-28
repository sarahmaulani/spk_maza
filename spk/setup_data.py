import os
import django
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spk_maza.settings')
django.setup()

from django.contrib.auth.models import User
from spk.models import Produk, Kriteria, NilaiProduk

def setup_data_awal():
    print("Mulai setup data...")
    
    admin_user = User.objects.first()
    
    kriteria_data = [
        {'kode': 'C1', 'nama': 'Jumlah Penjualan', 'bobot': 5, 'sifat': 'benefit', 'bisa_diinput_user': True},
        {'kode': 'C2', 'nama': 'Keuntungan per Unit', 'bobot': 4, 'sifat': 'benefit', 'bisa_diinput_user': False},
        {'kode': 'C3', 'nama': 'Rating Pelanggan', 'bobot': 4, 'sifat': 'benefit', 'bisa_diinput_user': True},
        {'kode': 'C4', 'nama': 'Biaya Produksi', 'bobot': 3, 'sifat': 'cost', 'bisa_diinput_user': False},
    ]
    
    for data in kriteria_data:
        Kriteria.objects.get_or_create(
            kode=data['kode'],
            defaults=data
        )
        print(f"Kriteria: {data['nama']}")
    
    produk_data = [
        {'nama': 'Bolu Pandan Srikaya', 'deskripsi': 'Bolu pandan dengan srikaya'},
        {'nama': 'Bolu Pandan', 'deskripsi': 'Bolu rasa pandan'},
        {'nama': 'Brownies', 'deskripsi': 'Brownies coklat lembut'},
    ]
    
    for data in produk_data:
        Produk.objects.get_or_create(
            nama=data['nama'],
            defaults=data
        )
        print(f"Produk: {data['nama']}")
    
    print("Setup selesai!")

if __name__ == '__main__':
    setup_data_awal()