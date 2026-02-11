"""
Market & Financial Services for Agri-Ledger.
Provides:
1. Mandi Price Comparison - Real-time market prices for crops
2. Profitability Forecaster - Historical ROI predictions
"""
import requests
import json
from decimal import Decimal
from django.db.models import Avg, Sum, F
from .models import CropCycle, Expense, Yield


# ============================================================
# 1. MANDI PRICE SERVICE
# ============================================================

# Fallback average prices (₹ per quintal) when API is unavailable
FALLBACK_MANDI_PRICES = {
    'wheat': {'min': 2100, 'max': 2400, 'modal': 2275, 'unit': 'Quintal'},
    'rice': {'min': 2200, 'max': 2800, 'modal': 2500, 'unit': 'Quintal'},
    'paddy': {'min': 2000, 'max': 2600, 'modal': 2300, 'unit': 'Quintal'},
    'maize': {'min': 1800, 'max': 2200, 'modal': 1962, 'unit': 'Quintal'},
    'cotton': {'min': 6200, 'max': 7100, 'modal': 6620, 'unit': 'Quintal'},
    'sugarcane': {'min': 310, 'max': 400, 'modal': 355, 'unit': 'Quintal'},
    'soybean': {'min': 3800, 'max': 4600, 'modal': 4300, 'unit': 'Quintal'},
    'mustard': {'min': 4800, 'max': 5650, 'modal': 5450, 'unit': 'Quintal'},
    'groundnut': {'min': 5200, 'max': 6300, 'modal': 5800, 'unit': 'Quintal'},
    'onion': {'min': 800, 'max': 2500, 'modal': 1500, 'unit': 'Quintal'},
    'potato': {'min': 600, 'max': 1500, 'modal': 1000, 'unit': 'Quintal'},
    'tomato': {'min': 500, 'max': 3000, 'modal': 1200, 'unit': 'Quintal'},
    'chana': {'min': 4400, 'max': 5200, 'modal': 4800, 'unit': 'Quintal'},
    'tur': {'min': 6000, 'max': 7500, 'modal': 6600, 'unit': 'Quintal'},
    'jowar': {'min': 2800, 'max': 3400, 'modal': 3100, 'unit': 'Quintal'},
    'bajra': {'min': 2200, 'max': 2700, 'modal': 2500, 'unit': 'Quintal'},
    'ragi': {'min': 3300, 'max': 3800, 'modal': 3578, 'unit': 'Quintal'},
    'barley': {'min': 1600, 'max': 2000, 'modal': 1735, 'unit': 'Quintal'},
}


def fetch_mandi_prices(crop_name, district='', state=''):
    """
    Fetch current mandi prices for a crop.
    
    Strategy:
    1. Try data.gov.in API for real-time prices
    2. Fall back to curated price data
    
    Returns:
        dict with keys: crop, district, prices (list of market entries), source
    """
    crop_lower = crop_name.strip().lower()
    
    # 1. Try data.gov.in API
    try:
        api_data = _fetch_from_data_gov(crop_name, district, state)
        if api_data and len(api_data) > 0:
            return {
                'crop': crop_name,
                'district': district or 'All India',
                'prices': api_data[:5],  # Top 5 markets
                'source': 'data.gov.in (Live)',
                'found': True
            }
    except Exception as e:
        print(f"data.gov.in API error: {e}")
    
    # 2. Fallback to curated data
    if crop_lower in FALLBACK_MANDI_PRICES:
        price_data = FALLBACK_MANDI_PRICES[crop_lower]
        return {
            'crop': crop_name,
            'district': district or 'All India',
            'prices': [{
                'market': district or 'Average Market',
                'min_price': price_data['min'],
                'max_price': price_data['max'],
                'modal_price': price_data['modal'],
                'unit': price_data['unit'],
            }],
            'source': 'MSP / Average Market Rates',
            'found': True
        }
    
    # 3. No data available
    return {
        'crop': crop_name,
        'district': district or 'Unknown',
        'prices': [],
        'source': 'No data available',
        'found': False
    }


def _fetch_from_data_gov(crop_name, district='', state=''):
    """
    Query data.gov.in for daily mandi prices.
    API: https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070
    """
    API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    API_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
    
    params = {
        'api-key': API_KEY,
        'format': 'json',
        'limit': 10,
        'filters[commodity]': crop_name.strip().title(),
    }
    
    if district:
        params['filters[district]'] = district.strip().title()
    if state:
        params['filters[state]'] = state.strip().title()
    
    response = requests.get(API_URL, params=params, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        records = data.get('records', [])
        
        results = []
        for record in records:
            results.append({
                'market': record.get('market', 'Unknown'),
                'min_price': int(record.get('min_price', 0)),
                'max_price': int(record.get('max_price', 0)),
                'modal_price': int(record.get('modal_price', 0)),
                'unit': 'Quintal',
                'state': record.get('state', ''),
                'arrival_date': record.get('arrival_date', ''),
            })
        
        return results
    
    return []


# ============================================================
# 2. PROFITABILITY FORECASTER
# ============================================================

def get_crop_forecast(crop_name, area_acres=1):
    """
    Predict profitability for a crop based on historical data.
    
    Uses past CropCycle records for the same crop to calculate:
    - Average expense per acre
    - Average income per acre
    - Estimated ROI
    
    Args:
        crop_name: Name of the crop
        area_acres: Planned area in acres
        
    Returns:
        dict with forecast data or None if insufficient data
    """
    crop_lower = crop_name.strip().lower()
    
    # Find all completed cycles for this crop (case-insensitive)
    completed_cycles = CropCycle.objects.filter(
        crop_name__iexact=crop_name.strip(),
        status='HARVESTED'
    )
    
    cycle_count = completed_cycles.count()
    
    if cycle_count == 0:
        # No historical data — use curated estimates
        return _get_estimated_forecast(crop_lower, area_acres)
    
    # Calculate averages from historical data
    total_expenses = Decimal('0')
    total_income = Decimal('0')
    total_area = Decimal('0')
    cycles_with_yield = 0
    
    for cycle in completed_cycles:
        cycle_expenses = Expense.objects.filter(cycle=cycle).aggregate(
            total=Sum('cost')
        )['total'] or Decimal('0')
        
        try:
            cycle_yield = Yield.objects.get(cycle=cycle)
            cycle_income = cycle_yield.selling_price or Decimal('0')
            cycles_with_yield += 1
        except Yield.DoesNotExist:
            cycle_income = Decimal('0')
        
        total_expenses += cycle_expenses
        total_income += cycle_income
        total_area += cycle.area_used
    
    if total_area == 0:
        return _get_estimated_forecast(crop_lower, area_acres)
    
    # Per-acre calculations
    avg_expense_per_acre = total_expenses / total_area
    avg_income_per_acre = total_income / total_area if cycles_with_yield > 0 else Decimal('0')
    avg_profit_per_acre = avg_income_per_acre - avg_expense_per_acre
    
    # Scale to planned area
    area = Decimal(str(area_acres))
    estimated_expense = avg_expense_per_acre * area
    estimated_income = avg_income_per_acre * area
    estimated_profit = avg_profit_per_acre * area
    
    # ROI percentage
    roi = (avg_profit_per_acre / avg_expense_per_acre * 100) if avg_expense_per_acre > 0 else Decimal('0')
    
    return {
        'crop': crop_name,
        'area': float(area),
        'data_source': 'historical',
        'cycle_count': cycle_count,
        'avg_expense_per_acre': round(float(avg_expense_per_acre), 2),
        'avg_income_per_acre': round(float(avg_income_per_acre), 2),
        'avg_profit_per_acre': round(float(avg_profit_per_acre), 2),
        'estimated_expense': round(float(estimated_expense), 2),
        'estimated_income': round(float(estimated_income), 2),
        'estimated_profit': round(float(estimated_profit), 2),
        'roi_percentage': round(float(roi), 1),
        'found': True,
    }


# Curated cost/revenue estimates per acre (in ₹)
CROP_ESTIMATES = {
    'wheat':      {'expense': 12000, 'income': 28000},
    'rice':       {'expense': 15000, 'income': 32000},
    'paddy':      {'expense': 14000, 'income': 30000},
    'maize':      {'expense': 10000, 'income': 22000},
    'cotton':     {'expense': 18000, 'income': 40000},
    'sugarcane':  {'expense': 25000, 'income': 55000},
    'soybean':    {'expense': 12000, 'income': 26000},
    'mustard':    {'expense': 10000, 'income': 24000},
    'groundnut':  {'expense': 16000, 'income': 35000},
    'onion':      {'expense': 20000, 'income': 45000},
    'potato':     {'expense': 18000, 'income': 38000},
    'tomato':     {'expense': 22000, 'income': 50000},
    'chana':      {'expense': 10000, 'income': 22000},
    'tur':        {'expense': 12000, 'income': 28000},
    'jowar':      {'expense': 8000,  'income': 18000},
    'bajra':      {'expense': 7000,  'income': 16000},
}


def _get_estimated_forecast(crop_lower, area_acres):
    """Return curated estimates when no historical data exists."""
    if crop_lower not in CROP_ESTIMATES:
        return {
            'crop': crop_lower.title(),
            'found': False,
            'message': 'No historical or estimated data available for this crop.'
        }
    
    est = CROP_ESTIMATES[crop_lower]
    area = float(area_acres)
    expense = est['expense']
    income = est['income']
    profit = income - expense
    roi = (profit / expense * 100) if expense > 0 else 0
    
    return {
        'crop': crop_lower.title(),
        'area': area,
        'data_source': 'estimated',
        'cycle_count': 0,
        'avg_expense_per_acre': expense,
        'avg_income_per_acre': income,
        'avg_profit_per_acre': profit,
        'estimated_expense': round(expense * area, 2),
        'estimated_income': round(income * area, 2),
        'estimated_profit': round(profit * area, 2),
        'roi_percentage': round(roi, 1),
        'found': True,
    }
