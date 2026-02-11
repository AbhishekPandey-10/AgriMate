from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import FarmerProfile, CropCycle, Expense, Yield
from datetime import datetime, timedelta
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Generate dummy farmers with historical data for demo purposes'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating dummy farmers...')
        
        # Clear existing dummy data (optional)
        User.objects.filter(username__startswith='demo').delete()
        
        # Farmer templates with different experience levels
        farmers = [
            {'name': 'Ram Singh', 'phone': 'demo9876543210', 'land': 25.5, 'years': 5},
            {'name': 'Shyam Kumar', 'phone': 'demo9876543211', 'land': 15.0, 'years': 3},
            {'name': 'Lakshmi Devi', 'phone': 'demo9876543212', 'land': 10.5, 'years': 2},
            {'name': 'Ganesh Patil', 'phone': 'demo9876543213', 'land': 30.0, 'years': 4},
            {'name': 'Sunita Sharma', 'phone': 'demo9876543214', 'land': 8.0, 'years': 1},
            {'name': 'Rajesh Yadav', 'phone': 'demo9876543215', 'land': 20.0, 'years': 3.5},
            {'name': 'Priya Reddy', 'phone': 'demo9876543216', 'land': 12.5, 'years': 1.5},
            {'name': 'Vijay Verma', 'phone': 'demo9876543217', 'land': 18.0, 'years': 2.5},
        ]
        
        # Common crop types
        crops = ['Wheat', 'Rice', 'Corn', 'Cotton', 'Sugarcane', 'Potato', 'Tomato', 'Onion']
        
        # Expense categories
        expense_types = [
            ('Seeds', 500, 5000),
            ('Fertilizer', 1000, 8000),
            ('Pesticide', 800, 4000),
            ('Labor', 2000, 15000),
            ('Irrigation', 1500, 6000),
            ('Equipment Rental', 3000, 10000),
        ]
        
        for farmer_data in farmers:
            # Create user
            user = User.objects.create_user(
                username=farmer_data['phone'],
                password='demo123',
                first_name=farmer_data['name']
            )
            
            # Create farmer profile
            farmer = FarmerProfile.objects.create(
                user=user,
                total_land_area=Decimal(str(farmer_data['land']))
            )
            
            self.stdout.write(f'  Created farmer: {farmer_data["name"]} ({farmer.farmer_code})')
            
            # Calculate how many months of history to generate
            months_history = int(farmer_data['years'] * 12)
            
            # Generate crops over time
            current_date = datetime.now()
            crops_created = 0
            
            for month_offset in range(0, months_history, 3):  # One crop every 3 months
                # Calculate start date
                start_date = current_date - timedelta(days=30 * month_offset)
                
                # Random crop
                crop_name = random.choice(crops)
                area = round(random.uniform(2.0, min(8.0, farmer_data['land'] / 2)), 2)
                
                # 70% of crops are harvested, 30% are still active
                is_active = month_offset < 6 and random.random() < 0.3
                status = 'ACTIVE' if is_active else 'HARVESTED'
                
                crop = CropCycle.objects.create(
                    farmer=farmer,
                    crop_name=crop_name,
                    area_used=Decimal(str(area)),
                    start_date=start_date.date(),
                    status=status
                )
                crops_created += 1
                
                # Add expenses for this crop
                num_expenses = random.randint(3, 8)
                total_expense = 0
                
                for i in range(num_expenses):
                    expense_name, min_cost, max_cost = random.choice(expense_types)
                    cost = round(random.uniform(min_cost, max_cost), 2)
                    expense_date = start_date + timedelta(days=random.randint(0, 60))
                    
                    Expense.objects.create(
                        cycle=crop,
                        item_name=expense_name,
                        cost=Decimal(str(cost)),
                        date=expense_date.date()
                    )
                    total_expense += cost
                
                # If harvested, add yield data
                if status == 'HARVESTED':
                    # Revenue is typically 1.5x to 3x of expenses for profit
                    revenue_multiplier = random.uniform(1.3, 2.8)
                    selling_price = round(total_expense * revenue_multiplier, 2)
                    harvest_date = start_date + timedelta(days=random.randint(90, 120))
                    
                    Yield.objects.create(
                        cycle=crop,
                        quantity_produced=Decimal(str(round(area * random.uniform(100, 500), 2))),
                        selling_price=Decimal(str(selling_price)),
                        date_sold=harvest_date.date()
                    )
            
            self.stdout.write(f'    > Created {crops_created} crops with expenses and yields')
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {len(farmers)} dummy farmers!'))
        self.stdout.write('Login credentials:')
        self.stdout.write('  Username: demo9876543210 to demo9876543217')
        self.stdout.write('  Password: demo123')
