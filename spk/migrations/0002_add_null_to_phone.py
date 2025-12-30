# spk/migrations/000X_add_null_to_phone.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('spk', '0002_add_alamat'),  # Ganti dengan migrasi terakhir Anda
    ]
    
    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='department',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='alamat',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
