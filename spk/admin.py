from django.contrib import admin
from .models import Produk, Kriteria, NilaiProduk, Periode 
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Produk, Kriteria, NilaiProduk, Periode, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'

class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active']
    list_filter = ['userprofile__role', 'is_staff', 'is_active']
    
    def get_role(self, obj):
        return obj.userprofile.role
    get_role.short_description = 'Role'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'department', 'created_at']
    list_filter = ['role', 'department']
    search_fields = ['user__username', 'user__email', 'phone']
    list_editable = ['role']

@admin.register(Periode)
class PeriodeAdmin(admin.ModelAdmin):
    list_display = ['nama', 'tanggal_mulai', 'tanggal_selesai', 'is_active', 'is_current']
    list_filter = ['is_active', 'tanggal_mulai']
    list_editable = ['is_active']
    search_fields = ['nama']

@admin.register(Produk)
class ProdukAdmin(admin.ModelAdmin):
    list_display = ['nama', 'deskripsi']
    search_fields = ['nama']

@admin.register(Kriteria)
class KriteriaAdmin(admin.ModelAdmin):
    list_display = ['kode', 'nama', 'bobot', 'sifat', 'bisa_diinput_user', 'deskripsi']
    list_filter = ['sifat', 'bisa_diinput_user']
    list_editable = ['bisa_diinput_user']

@admin.register(NilaiProduk)
class NilaiProdukAdmin(admin.ModelAdmin):
    list_display = ['produk', 'kriteria', 'periode', 'nilai', 'created_by', 'created_at']
    list_filter = ['kriteria', 'produk', 'periode', 'created_by']
    search_fields = ['produk__nama']
    readonly_fields = ['created_by', 'created_at']