import numpy as np
from .models import Produk, Kriteria, NilaiProduk, Periode

def hitung_topsis(periode_id=None):
    """
    Menghitung ranking produk menggunakan metode TOPSIS
    berdasarkan periode tertentu
    """
    try:
        # Tentukan periode
        if periode_id:
            periode = Periode.objects.get(id=periode_id)
        else:
            # Ambil periode aktif terbaru
            periode = Periode.objects.filter(is_active=True).order_by('-tanggal_mulai').first()
        
        if not periode:
            print("Tidak ada periode aktif")
            return []
        
        print(f"Memproses TOPSIS untuk periode: {periode.nama}")
        
        # 1. AMBIL DATA DARI DATABASE untuk periode tertentu
        produk_list = list(Produk.objects.all())
        kriteria_list = list(Kriteria.objects.all().order_by('kode'))
        
        if not produk_list or not kriteria_list:
            print("Tidak ada data produk atau kriteria")
            return []
        
        # 2. BUAT MATRIKS KEPUTUSAN (Produk x Kriteria)
        matriks_keputusan = []
        nama_produk_list = []
        
        for produk in produk_list:
            baris = []
            for kriteria in kriteria_list:
                try:
                    # Cari nilai produk untuk kriteria ini di periode tertentu
                    nilai_obj = NilaiProduk.objects.get(
                        produk=produk, 
                        kriteria=kriteria,
                        periode=periode
                    )
                    baris.append(float(nilai_obj.nilai))
                except NilaiProduk.DoesNotExist:
                    # Jika tidak ada data, beri nilai default 0
                    baris.append(0.0)
            
            matriks_keputusan.append(baris)
            nama_produk_list.append(produk.nama)
        
        # Konversi ke numpy array
        X = np.array(matriks_keputusan, dtype=float)
        print(f"Matriks keputusan: {X.shape} untuk {len(produk_list)} produk")
        
        # 3. NORMALISASI MATRIKS
        pembagi = np.sqrt(np.sum(X**2, axis=0))
        pembagi[pembagi == 0] = 1e-10
        matriks_normalisasi = X / pembagi
        
        # 4. MATRIKS BOBOT
        bobot_kriteria = np.array([k.bobot for k in kriteria_list])
        matriks_terbobot = matriks_normalisasi * bobot_kriteria
        
        # 5. SOLUSI IDEAL
        solusi_ideal_positif = []
        solusi_ideal_negatif = []
        
        for i, kriteria in enumerate(kriteria_list):
            if kriteria.sifat == 'benefit':
                solusi_ideal_positif.append(np.max(matriks_terbobot[:, i]))
                solusi_ideal_negatif.append(np.min(matriks_terbobot[:, i]))
            else:  # cost
                solusi_ideal_positif.append(np.min(matriks_terbobot[:, i]))
                solusi_ideal_negatif.append(np.max(matriks_terbobot[:, i]))
        
        A_plus = np.array(solusi_ideal_positif)
        A_minus = np.array(solusi_ideal_negatif)
        
        # 6. HITUNG JARAK KE SOLUSI IDEAL
        D_plus = np.sqrt(np.sum((matriks_terbobot - A_plus)**2, axis=1))
        D_minus = np.sqrt(np.sum((matriks_terbobot - A_minus)**2, axis=1))
        
        # 7. NILAI PREFERENSI
        nilai_preferensi = D_minus / (D_plus + D_minus + 1e-10)
        
        # 8. RANKING
        hasil_akhir = []
        for i, nama_produk in enumerate(nama_produk_list):
            hasil_akhir.append({
                'produk': nama_produk,
                'nilai': float(nilai_preferensi[i]),
                'rank': 0,
                'periode': periode.nama  
            })
        
        # Urutkan berdasarkan nilai preferensi (descending)
        hasil_akhir.sort(key=lambda x: x['nilai'], reverse=True)
        
        # Beri peringkat
        for i, item in enumerate(hasil_akhir):
            item['rank'] = i + 1
        
        print(f"Perhitungan TOPSIS selesai untuk periode {periode.nama}")
        return hasil_akhir
        
    except Exception as e:
        print(f"Error dalam hitung_topsis: {e}")
        return []