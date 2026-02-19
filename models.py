from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import uuid

# 1. Farmer Profile: Stores the unique ID and Land info
class FarmerProfile(models.Model):
    CATEGORY_CHOICES = [
        ('GENERAL', 'General'),
        ('SC', 'Scheduled Caste'),
        ('ST', 'Scheduled Tribe'),
        ('OBC', 'Other Backward Class'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    farmer_code = models.CharField(max_length=10, unique=True, editable=False)
    total_land_area = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Fields for scheme targeting
    state = models.CharField(max_length=100, blank=True, default='')
    district = models.CharField(max_length=100, blank=True, default='')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='GENERAL')
    has_kcc = models.BooleanField(default=False, help_text="Has Kisan Credit Card")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.farmer_code:
            self.farmer_code = "FMR-" + str(uuid.uuid4())[:4].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} ({self.farmer_code})"

    def get_free_land(self):
        used = self.cropcycle_set.filter(status='ACTIVE').aggregate(models.Sum('area_used'))['area_used__sum'] or 0
        return self.total_land_area - used

# 2. Crop Cycle: Manages active vs harvested land
class CropCycle(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'In the Field'),
        ('HARVESTED', 'Harvested & Sold'),
    ]
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE)
    crop_name = models.CharField(max_length=100)
    area_used = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Skip validation if farmer not assigned yet (e.g., during form creation)
        if not self.farmer_id:
            return
        
        if self.status == 'ACTIVE':
            used = self.farmer.cropcycle_set.filter(status='ACTIVE').exclude(pk=self.pk).aggregate(models.Sum('area_used'))['area_used__sum'] or 0
            if (used + self.area_used) > self.farmer.total_land_area:
                 raise ValidationError(f"Insufficient Land! Free space: {self.farmer.get_free_land()}")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.crop_name} ({self.status})"

# 3. Expense: Tracks spending per crop
class Expense(models.Model):
    cycle = models.ForeignKey(CropCycle, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

# 4. Yield: Tracks income
class Yield(models.Model):
    cycle = models.OneToOneField(CropCycle, on_delete=models.CASCADE)
    quantity_produced = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    sold_receipt = models.ImageField(upload_to='sales/', null=True, blank=True)
    date_sold = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

# 5. Scheme Recommendation: AI-generated government scheme suggestions
class SchemeRecommendation(models.Model):
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='scheme_recommendations')
    scheme_name = models.CharField(max_length=200)
    description = models.TextField()
    benefits = models.TextField()
    eligibility_criteria = models.TextField()
    link = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.scheme_name} - {self.farmer.farmer_code}"
