from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Sum
from xhtml2pdf import pisa
from io import BytesIO
from .models import CropCycle, Expense, FarmerProfile, Yield, SchemeRecommendation
from .forms import CropForm, ExpenseForm, YieldForm
from .gemini_service import fetch_schemes_smartly

def signup(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        name = request.POST.get('name')
        password = request.POST.get('password')
        land_area = request.POST.get('land_area', '0')
        # language = request.POST.get('language') # Not used yet
        # otp = request.POST.get('otp') # Not used yet

        if User.objects.filter(username=phone).exists():
            messages.error(request, "Phone number already registered.")
            return redirect('login')

        try:
            # Create User
            user = User.objects.create_user(username=phone, password=password, first_name=name)
            
            # Create Farmer Profile with provided land area
            FarmerProfile.objects.create(user=user, total_land_area=float(land_area))
            
            # Login
            login(request, user)
            messages.success(request, f"Welcome, {name}!")
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"Signup failed: {e}")
            return redirect('login')

    return redirect('login')


# 1. The Dashboard (Home)
@login_required
def dashboard(request):
    try:
        farmer = request.user.farmerprofile
    except:
        return render(request, 'core/error.html', {'message': 'No Farmer Profile Found. Please contact Admin.'})
    
    # Get Data
    active_crops = CropCycle.objects.filter(farmer=farmer, status='ACTIVE')
    recent_expenses = Expense.objects.filter(cycle__farmer=farmer).order_by('-date')[:5]
    recommended_schemes = SchemeRecommendation.objects.filter(farmer=farmer, is_active=True).order_by('-created_at')[:5]
    
    context = {
        'farmer': farmer,
        'active_crops': active_crops,
        'expenses': recent_expenses,
        'recommended_schemes': recommended_schemes,
        'free_land': farmer.get_free_land()
    }
    return render(request, 'core/dashboard.html', context)

# 2. Add New Crop (Start Season)
@login_required
def crop_add(request):
    if request.method == 'POST':
        form = CropForm(request.POST)
        if form.is_valid():
            try:
                crop = form.save(commit=False)
                crop.farmer = request.user.farmerprofile
                crop.save()
                
                # --- GEMINI INTEGRATION: Fetch Government Schemes ---
                try:
                    # 1. Fetch clean data using structured schema
                    data = fetch_schemes_smartly(crop.farmer, crop)
                    
                    # 2. Bulk Create (Much faster than looping and saving one by one)
                    schemes_to_create = []
                    
                    for item in data.get('recommendations', []):
                        schemes_to_create.append(
                            SchemeRecommendation(
                                farmer=crop.farmer,
                                scheme_name=item.get('scheme_name', 'Unknown Scheme'),
                                description=item.get('description', ''),
                                benefits=item.get('benefits', ''),
                                eligibility_criteria=item.get('eligibility_criteria', ''),
                                link=item.get('application_link', '')
                            )
                        )
                    
                    # 3. Save all at once to SQL
                    if schemes_to_create:
                        SchemeRecommendation.objects.bulk_create(schemes_to_create)
                        messages.success(request, f"New season started! Found {len(schemes_to_create)} relevant schemes.")
                    else:
                        messages.success(request, "New season started!")
                    
                except Exception as e:
                    # Log error but don't stop the user flow
                    print(f"Scheme fetch failed: {e}")
                    messages.success(request, "New season started!")
                
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Error: {e}")
    else:
        form = CropForm()
    return render(request, 'core/crop_form.html', {'form': form, 'title': 'Start New Crop'})

# 3. Add Expense (Money Out)
@login_required
def expense_add(request):
    if request.method == 'POST':
        form = ExpenseForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense logged successfully.")
            return redirect('dashboard')
    else:
        form = ExpenseForm(request.user)
    return render(request, 'core/expense_form.html', {'form': form, 'title': 'Log Expense'})

# 4. Harvest Logic (Close Cycle)
@login_required
def crop_harvest(request, cycle_id):
    cycle = get_object_or_404(CropCycle, id=cycle_id, farmer__user=request.user)
    
    if request.method == 'POST':
        form = YieldForm(request.POST, request.FILES)
        if form.is_valid():
            # Save Yield Data
            income = form.save(commit=False)
            income.cycle = cycle
            income.save()
            
            # Close the Cycle (Free up land)
            cycle.status = 'HARVESTED'
            cycle.save()
            
            messages.success(request, "Crop harvested and land released!")
            return redirect('dashboard')
    else:
        form = YieldForm()
    return render(request, 'core/harvest_form.html', {'form': form, 'title': f'Harvest {cycle.crop_name}'})

# 5. Generate PDF Bank Report
@login_required
def generate_pdf(request):
    try:
        farmer = request.user.farmerprofile
    except:
        return HttpResponse("No Farmer Profile Found", status=404)
    
    # Get data for the report
    crops = CropCycle.objects.filter(farmer=farmer).order_by('-start_date')[:10]
    expenses = Expense.objects.filter(cycle__farmer=farmer).order_by('-date')[:10]
    
    # Calculate financial summary
    total_income = Yield.objects.filter(cycle__farmer=farmer).aggregate(
        total=Sum('selling_price')
    )['total'] or 0
    
    total_expenses = Expense.objects.filter(cycle__farmer=farmer).aggregate(
        total=Sum('cost')
    )['total'] or 0
    
    net_profit = total_income - total_expenses
    active_crop_count = CropCycle.objects.filter(farmer=farmer, status='ACTIVE').count()
    
    # Simple credit score calculation (0-100)
    # Based on: number of crops, profit, and activity
    credit_score = min(100, (
        (crops.count() * 10) +  # 10 points per crop (max 100)
        (20 if net_profit > 0 else 0) +  # 20 points for positive profit
        (active_crop_count * 5)  # 5 points per active crop
    ))
    
    context = {
        'farmer': farmer,
        'crops': crops,
        'expenses': expenses,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'active_crop_count': active_crop_count,
        'credit_score': credit_score,
        'report_date': timezone.now(),
    }
    
    # Render HTML template
    html_string = render_to_string('core/report_template.html', context)
    
    # Generate PDF using xhtml2pdf
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)
    
    if pdf.err:
        return HttpResponse('Error generating PDF', status=500)
    
    # Return PDF as response
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="credit_report_{farmer.farmer_code}.pdf"'
    
    return response
