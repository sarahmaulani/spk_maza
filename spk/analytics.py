import json
from django.db.models import Avg, Sum, Count
from .models import Produk, Kriteria, NilaiProduk, Periode
from django.db import models



def get_sales_analytics(periode_count=4):
    """Analytics data penjualan"""
    periods = list(Periode.objects.all().order_by('-tanggal_mulai')[:periode_count])
    periods.reverse()

    sales_kriteria = Kriteria.objects.get(kode='C1')
    
    analytics_data = {
        'labels': [p.nama for p in periods],
        'datasets': []
    }
    
    # tampilin 5 produk pling atas
    top_products = Produk.objects.annotate(
        total_penjualan=Sum(
            'nilaiproduk__nilai',
            filter=models.Q(nilaiproduk__kriteria__kode='C1')
        )
    ).order_by('-total_penjualan')[:5]

    
    for product in top_products:
        product_data = []
        for period in periods:
            try:
                nilai = NilaiProduk.objects.get(
                    produk=product,
                    kriteria=sales_kriteria,
                    periode=period
                ).nilai
                product_data.append(nilai)
            except NilaiProduk.DoesNotExist:
                product_data.append(0)
        
        analytics_data['datasets'].append({
            'label': product.nama,
            'data': product_data,
            'borderColor': get_chart_color(len(analytics_data['datasets'])),
            'backgroundColor': get_chart_color(len(analytics_data['datasets']), 0.1),
        })
    
    return analytics_data

def get_performance_comparison(periode_awal, periode_akhir):
    """Perbandingan performa antar periode"""
    hasil_awal = periode_awal.get_ranking_data() if periode_awal else []
    hasil_akhir = periode_akhir.get_ranking_data() if periode_akhir else []
    
    comparison = []
    
    for hasil in hasil_akhir:
        produk_nama = hasil['produk']
        rank_akhir = hasil['rank']
        nilai_akhir = hasil['nilai']
        
        # Cari ranking di periode awal
        rank_awal = None
        nilai_awal = None
        for h in hasil_awal:
            if h['produk'] == produk_nama:
                rank_awal = h['rank']
                nilai_awal = h['nilai']
                break
        
        # itung perubahan
        perubahan_rank = rank_awal - rank_akhir if rank_awal else 0
        status = "naik" if perubahan_rank > 0 else "turun" if perubahan_rank < 0 else "stabil"
        
        comparison.append({
            'produk': produk_nama,
            'rank_awal': rank_awal,
            'rank_akhir': rank_akhir,
            'nilai_awal': nilai_awal,
            'nilai_akhir': nilai_akhir,
            'perubahan_rank': perubahan_rank,
            'status': status
        })
    
    return sorted(comparison, key=lambda x: abs(x['perubahan_rank']), reverse=True)

def get_top_performers(periode, limit=5):
    hasil = periode.get_ranking_data() if periode else []
    return sorted(hasil, key=lambda x: x['nilai'], reverse=True)[:limit]


def get_improvement_analysis():
    """Analisis improvement produk"""
    periode_aktif = Periode.objects.filter(is_active=True).first()
    periode_sebelumnya = periode_aktif.get_periode_sebelumnya() if periode_aktif else None
    
    if not periode_sebelumnya:
        return []
    
    comparison = get_performance_comparison(periode_sebelumnya, periode_aktif)
    
    # Ambil yang mna yg paling berkembang
    improvements = [c for c in comparison if c['perubahan_rank'] > 0]
    return sorted(improvements, key=lambda x: x['perubahan_rank'], reverse=True)[:5]

def get_chart_color(index, opacity=1):
    """Generate warna untuk chart"""
    colors = [
        f'rgba(54, 162, 235, {opacity})',   # biru
        f'rgba(255, 99, 132, {opacity})',   # merah
        f'rgba(75, 192, 192, {opacity})',   # ijo
        f'rgba(255, 159, 64, {opacity})',   # orange
        f'rgba(153, 102, 255, {opacity})',  # ungu
        f'rgba(255, 205, 86, {opacity})',   # kuning
        f'rgba(201, 203, 207, {opacity})',  # abu
    ]
    return colors[index % len(colors)]

def get_kriteria_analysis(periode):
    """Analisis pengaruh tiap kriteria terhadap ranking"""
    if not periode:
        return {}
    
    # itung hubungan antara nilai kriteria dan ranking akhir
    analysis = {}
    kriteria_list = Kriteria.objects.all()
    
    for kriteria in kriteria_list:
        # Ambil semua nilai untuk kriteria ini di periode tertentu
        nilai_data = NilaiProduk.objects.filter(
            kriteria=kriteria,
            periode=periode
        ).select_related('produk')
        
        # buat analisis sederhana, kita hitung rata-rata nilai per produk
        analysis[kriteria.nama] = {
            'bobot': kriteria.bobot,
            'sifat': kriteria.sifat,
            'rata_rata': nilai_data.aggregate(Avg('nilai'))['nilai__avg'] or 0,
            'total_data': nilai_data.count()
        }
    
    return analysis