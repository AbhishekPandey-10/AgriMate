from django import forms
from .models import CropCycle, Expense, Yield

class CropForm(forms.ModelForm):
    class Meta:
        model = CropCycle
        fields = ['crop_name', 'area_used', 'start_date', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'crop_name': forms.TextInput(attrs={'class': 'form-control'}),
            'area_used': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['cycle', 'item_name', 'cost', 'date', 'receipt_image']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'cycle': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FILTER LOGIC: Only show THIS farmer's active crops in the dropdown
        if hasattr(user, 'farmerprofile'):
            self.fields['cycle'].queryset = CropCycle.objects.filter(farmer__user=user, status='ACTIVE')

class YieldForm(forms.ModelForm):
    class Meta:
        model = Yield
        fields = ['quantity_produced', 'selling_price', 'date_sold', 'sold_receipt']
        widgets = {
            'date_sold': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'quantity_produced': forms.NumberInput(attrs={'class': 'form-control'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }
