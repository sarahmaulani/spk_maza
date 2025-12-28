from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('staff', 'Staff Input Data'),
        ('viewer', 'Viewer Only'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    #mo nampilin username sama roleny
    def __str__(self):
        return f"{self.user.username} ({self.role})"
    
    # role nya apa yang bisa di akses pun apa
    def is_admin(self):
        return self.role == 'admin'
    
    def is_staff_user(self):
        return self.role in ['admin', 'staff']
    
    def can_input_data(self):
        return self.role in ['admin', 'staff']
    
    def can_view_reports(self):
        return self.role in ['admin', 'staff', 'viewer']

# periode waktu u/ penilaian
class Periode(models.Model):
    nama = models.CharField(max_length=100) 
    tanggal_mulai = models.DateField()
    tanggal_selesai = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    #urutin periode terbaru
    class Meta:
        ordering = ['-tanggal_mulai']
   #tampilin status dan nama perode
    def __str__(self):
        status = "(aktif)" if self.is_active else "(non-Aktif)"
        return f"{status} {self.nama}"
   
     # fungsi buat cek apakah periode lg berjalan?
    def is_current(self):
        """Cek apakah periode sedang berjalan"""
        today = timezone.now().date()
        return self.tanggal_mulai <= today <= self.tanggal_selesai
    #ambil data ranking
    def get_ranking_data(self):
        from .utils import hitung_topsis
        return hitung_topsis(self.id)
    #ambil periode sebelumnya
    def get_periode_sebelumnya(self):
        return Periode.objects.filter(
            tanggal_mulai__lt=self.tanggal_mulai
        ).order_by('-tanggal_mulai').first()
    
    # produk (termasuk apa yang dinilai)
class Produk(models.Model):
    nama = models.CharField(max_length=150)
    deskripsi = models.TextField(blank=True)
    #tampilin nama prduk
    def __str__(self):
        return self.nama
    #ambil kriteria dengan code c3 = RATING PELANGGAN
    def get_avg_rating(self, periode=None):
        from .models import NilaiProduk, Kriteria
        try:
            rating_kriteria = Kriteria.objects.get(kode='C3')  
            query = NilaiProduk.objects.filter(
                produk=self, 
                kriteria=rating_kriteria
            )
            if periode:
                query = query.filter(periode=periode)
            #hitung rata" 
            avg = query.aggregate(models.Avg('nilai'))['nilai__avg']
            return round(avg, 2) if avg else 0
        except:
            return 0
    #Pakai metode ini untk mengambil tren penjualan bebrapa period
    def get_sales_trend(self, periode_count=4):
        """Trend penjualan produk dalam beberapa periode terakhir"""
        from .models import NilaiProduk, Kriteria, Periode
        try:
            sales_kriteria = Kriteria.objects.get(kode='C1')  # Jumlah Penjualan
            periods = Periode.objects.all().order_by('-tanggal_mulai')[:periode_count]
            
            trend_data = []
            for period in periods:
                try:
                    nilai = NilaiProduk.objects.get(
                        produk=self,
                        kriteria=sales_kriteria,
                        periode=period
                    ).nilai
                    trend_data.append({
                        'periode': period.nama,
                        'penjualan': nilai
                    })
                except NilaiProduk.DoesNotExist:
                    trend_data.append({
                        'periode': period.nama,
                        'penjualan': 0
                    })
            
            return trend_data
        except:
            return []

#kriteria yang dipakai dalam perhitungan spk
class Kriteria(models.Model):
    SIFAT_CHOICES = [
        ('benefit', 'Benefit'),
        ('cost', 'Cost'),
    ]
    
    nama = models.CharField(max_length=100)
    kode = models.CharField(max_length=10, unique=True)
    bobot = models.FloatField(default=1)
    sifat = models.CharField(max_length=20, choices=SIFAT_CHOICES)
    deskripsi = models.TextField(blank=True)
    #cuma kriteria tertentu yg bisa di input user
    bisa_diinput_user = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.kode}: {self.nama} ({self.bobot})"
#tabel yg menghubungkan produk + kriteria + periode
class NilaiProduk(models.Model):
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    kriteria = models.ForeignKey(Kriteria, on_delete=models.CASCADE)
    nilai = models.FloatField()
    periode = models.ForeignKey(Periode, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
     #tdk ada yg boleh duplikat
    class Meta:
        unique_together = ('produk', 'kriteria', 'periode') 
    
    def __str__(self):
        return f"{self.produk.nama} - {self.kriteria.nama} ({self.periode.nama}): {self.nilai}"
    
