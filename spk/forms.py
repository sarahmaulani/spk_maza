from django import forms
from .models import NilaiProduk, Produk, Kriteria

class InputNilaiForm(forms.ModelForm):
    class Meta:
        model = NilaiProduk
        fields = ['produk', 'kriteria', 'nilai']
        widgets = {
            'produk': forms.Select(attrs={'class': 'form-control'}),
            'kriteria': forms.Select(attrs={'class': 'form-control'}),
            'nilai': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hanya tampilkan kriteria yang bisa diinput user
        self.fields['kriteria'].queryset = Kriteria.objects.filter(bisa_diinput_user=True)