from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
import json
from .models import Produk, Kriteria, NilaiProduk, Periode, UserProfile
from .utils import hitung_topsis
from .analytics import (
    get_sales_analytics, 
    get_performance_comparison,
    get_top_performers,
    get_improvement_analysis,
    get_kriteria_analysis
)

def user_login(request):
    """Handle user login dengan role check"""
    if request.user.is_authenticated:
        return redirect('user_home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                try:
                    profile = UserProfile.objects.get(user=user)
                    role_display = dict(UserProfile.ROLE_CHOICES).get(profile.role, 'User')
                    messages.success(request, f'Selamat datang, {user.username}! ({role_display})')
                except UserProfile.DoesNotExist:
                    messages.success(request, f'Selamat datang, {user.username}!')
                
                return redirect('user_home')
            else:
                messages.error(request, 'Akun tidak aktif.')
        else:
            messages.error(request, 'Username atau password salah!')
    
    return render(request, 'spk/login.html')

def user_logout(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'Anda telah berhasil logout.')
    return redirect('login')

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                if user_profile.role in allowed_roles or user_profile.role == 'admin':
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
                    return redirect('user_home')
            except UserProfile.DoesNotExist:
                messages.error(request, 'Profile user tidak ditemukan.')
                return redirect('user_home')
        return wrapper
    return decorator

@login_required
def user_home(request):
    """Dashboard utama - accessible by all roles"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        
        periode_aktif = Periode.objects.filter(is_active=True).order_by('-tanggal_mulai').first()
        semua_periode = Periode.objects.all().order_by('-tanggal_mulai')
        
        hasil_topsis = hitung_topsis(periode_aktif.id if periode_aktif else None)
        hasil_json = json.dumps(hasil_topsis)
        
        sales_analytics = get_sales_analytics() if user_profile.is_staff_user() else {}
        top_performers = get_top_performers(periode_aktif) if user_profile.is_staff_user() else []
        improvements = get_improvement_analysis() if user_profile.is_staff_user() else []
        kriteria_analysis = get_kriteria_analysis(periode_aktif) if user_profile.is_staff_user() else {}
        
        total_produk = Produk.objects.count()
        total_nilai = NilaiProduk.objects.count()
        nilai_user = NilaiProduk.objects.filter(created_by=request.user).count()
        
        context = {
            'hasil': hasil_topsis,
            'hasil_json': hasil_json,
            'user': request.user,
            'user_profile': user_profile,
            'total_produk': total_produk,
            'total_nilai': total_nilai,
            'nilai_user': nilai_user,
            'periode_aktif': periode_aktif,
            'semua_periode': semua_periode,
            'sales_analytics_json': json.dumps(sales_analytics),
            'top_performers': top_performers,
            'improvements': improvements,
            'kriteria_analysis': kriteria_analysis,
        }
        return render(request, 'spk/home.html', context)
        
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile user tidak ditemukan. Silakan hubungi admin.')
        return redirect('logout')
    except Exception as e:
        print(f"Error di home: {e}")
        context = {
            'hasil': [],
            'hasil_json': '[]',
            'user': request.user,
            'user_profile': None,
            'total_produk': 0,
            'total_nilai': 0,
            'nilai_user': 0,
            'periode_aktif': None,
            'semua_periode': [],
            'sales_analytics_json': '{}',
            'top_performers': [],
            'improvements': [],
            'kriteria_analysis': {},
        }
        return render(request, 'spk/home.html', context)

@role_required(['admin', 'staff', 'viewer'])
def hasil_topsis(request, periode_id=None):
    """Halaman hasil TOPSIS - accessible by all roles"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        
        if periode_id:
            periode = get_object_or_404(Periode, id=periode_id)
        else:
            periode = Periode.objects.filter(is_active=True).order_by('-tanggal_mulai').first()
        
        semua_periode = Periode.objects.all().order_by('-tanggal_mulai')
        hasil_topsis = hitung_topsis(periode.id if periode else None)
        
        context = {
            'hasil': hasil_topsis,
            'user': request.user,
            'user_profile': user_profile,
            'periode_terpilih': periode,
            'semua_periode': semua_periode,
        }
        return render(request, 'spk/hasil_topsis.html', context)
        
    except Exception as e:
        print(f"Error di hasil_topsis: {e}")
        context = {
            'hasil': [],
            'user': request.user,
            'user_profile': None,
            'periode_terpilih': None,
            'semua_periode': [],
        }
        return render(request, 'spk/hasil_topsis.html', context)

@role_required(['admin', 'staff'])
def input_nilai(request):
    """Halaman input nilai - hanya untuk admin & staff"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        
        if not user_profile.can_input_data():
            messages.error(request, 'Anda tidak memiliki izin untuk input data.')
            return redirect('user_home')
        
        periode_aktif = Periode.objects.filter(is_active=True).order_by('-tanggal_mulai').first()
        
        if not periode_aktif:
            messages.error(request, 'Tidak ada periode aktif. Silakan hubungi admin.')
            return redirect('user_home')
        
        kriteria_user = Kriteria.objects.filter(bisa_diinput_user=True)
        
        if request.method == 'POST':
            produk_id = request.POST.get('produk')
            kriteria_id = request.POST.get('kriteria')
            nilai = request.POST.get('nilai')
            
            try:
                produk = Produk.objects.get(id=produk_id)
                kriteria = Kriteria.objects.get(id=kriteria_id)
                
                nilai_obj, created = NilaiProduk.objects.update_or_create(
                    produk=produk,
                    kriteria=kriteria,
                    periode=periode_aktif,
                    defaults={
                        'nilai': nilai,
                        'created_by': request.user
                    }
                )
                
                if created:
                    messages.success(request, f'Data {produk.nama} - {kriteria.nama} berhasil disimpan!')
                else:
                    messages.success(request, f'Data {produk.nama} - {kriteria.nama} berhasil diupdate!')
                    
                return redirect('input_nilai')
                
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        
        nilai_user = NilaiProduk.objects.filter(
            created_by=request.user, 
            periode=periode_aktif
        ).select_related('produk', 'kriteria')
        
        context = {
            'produk_list': Produk.objects.all(),
            'kriteria_user': kriteria_user,
            'nilai_user': nilai_user,
            'user': request.user,
            'user_profile': user_profile,
            'periode_aktif': periode_aktif,
        }
        return render(request, 'spk/input_nilai.html', context)
        
    except Exception as e:
        print(f"Error di input_nilai: {e}")
        messages.error(request, 'Terjadi error saat mengakses halaman input data.')
        return redirect('user_home')

@role_required(['admin', 'staff'])
def analytics_dashboard(request):
    """Halaman analytics - hanya untuk admin & staff"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        periode_aktif = Periode.objects.filter(is_active=True).order_by('-tanggal_mulai').first()
        semua_periode = Periode.objects.all().order_by('-tanggal_mulai')
        
        sales_analytics = get_sales_analytics()
        improvements = get_improvement_analysis()
        kriteria_analysis = get_kriteria_analysis(periode_aktif)
        
        periode_sebelumnya = periode_aktif.get_periode_sebelumnya() if periode_aktif else None
        performance_comparison = get_performance_comparison(periode_sebelumnya, periode_aktif)
        
        context = {
            'user': request.user,
            'user_profile': user_profile,
            'periode_aktif': periode_aktif,
            'semua_periode': semua_periode,
            'periode_sebelumnya': periode_sebelumnya,
            'sales_analytics_json': json.dumps(sales_analytics),
            'improvements': improvements,
            'kriteria_analysis': kriteria_analysis,
            'performance_comparison': performance_comparison,
        }
        return render(request, 'spk/analytics.html', context)
        
    except Exception as e:
        print(f"Error di analytics: {e}")
        messages.error(request, 'Terjadi error saat memuat data analytics.')
        return redirect('user_home')

@role_required(['admin', 'staff'])
def export_report(request, report_type='ranking'):
    """Export laporan - hanya untuk admin & staff"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        periode_aktif = Periode.objects.filter(is_active=True).order_by('-tanggal_mulai').first()
        
        if report_type == 'ranking':
            data = hitung_topsis(periode_aktif.id if periode_aktif else None)
            filename = f'ranking_report_{periode_aktif.nama if periode_aktif else "all"}.json'
        
        elif report_type == 'analytics':
            data = {
                'sales_analytics': get_sales_analytics(),
                'improvements': get_improvement_analysis(),
                'kriteria_analysis': get_kriteria_analysis(periode_aktif),
            }
            filename = f'analytics_report_{periode_aktif.nama if periode_aktif else "all"}.json'
        
        else:
            messages.error(request, 'Jenis report tidak valid.')
            return redirect('analytics_dashboard')
        
        response = JsonResponse(data, safe=False)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        messages.success(request, f'Report {report_type} berhasil diexport!')
        return response
        
    except Exception as e:
        print(f"Error export report: {e}")
        messages.error(request, 'Terjadi error saat export report.')
        return redirect('analytics_dashboard')

def index(request):
    return redirect('login')