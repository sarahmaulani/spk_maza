from django.urls import path
from .views import (
    user_home, 
    user_login, 
    user_logout,  
    hasil_topsis, 
    index, 
    input_nilai, 
    analytics_dashboard, 
    export_report
)

urlpatterns = [
    path('', index, name='index'),
    path('home/', user_home, name='user_home'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),  
    path('hasil/', hasil_topsis, name='hasil_topsis'),
    path('hasil/<int:periode_id>/', hasil_topsis, name='hasil_topsis_periode'),
    path('input-nilai/', input_nilai, name='input_nilai'),
    path('analytics/', analytics_dashboard, name='analytics_dashboard'),
    path('export/<str:report_type>/', export_report, name='export_report'),
]