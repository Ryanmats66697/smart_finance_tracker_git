from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from tracker.models import Category, Expense, Income
from decimal import Decimal
from datetime import datetime
import random

class Command(BaseCommand):
    help = 'Adds fake income and expense data for john_doe for all months of 2024'

    def handle(self, *args, **kwargs):
        self.stdout.write('Adding income and expense data for john_doe for 2024...')
        
        # Get the john_doe user
        try:
            user = User.objects.get(username='john_doe')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User john_doe does not exist. Please run setup_test_data first.'))
            return
        
        # Get or create categories
        categories = self._get_or_create_categories(user)
        
        # Create income and expenses for all months of 2024
        for month in range(1, 13):  # 1 = January, 12 = December
            self._create_monthly_data(user, categories, month)
        
        self.stdout.write(self.style.SUCCESS('Successfully added income and expense data for john_doe for 2024'))

    def _get_or_create_categories(self, user):
        categories = []
        category_data = [
            ('Rent', True, 18000),
            ('Groceries', False, 10000),
            ('Transportation', False, 7000),
            ('Entertainment', False, 4000),
            ('Utilities', True, 12000),
            ('Shopping', False, 8000),
            ('Dining Out', False, 5000),
            ('Healthcare', False, 2000),
            ('Education', False, 3000),
            ('Travel', False, 6000)
        ]
        
        for name, is_fixed, default_amount in category_data:
            category, created = Category.objects.get_or_create(
                name=name,
                user=user,
                defaults={
                    'description': f'{name} expenses',
                    'is_fixed_expense': is_fixed
                }
            )
            categories.append((category, is_fixed, default_amount))
        
        return categories

    def _create_monthly_data(self, user, categories, month):
        # Set the date to the 15th of each month in 2024
        date = datetime(2024, month, 15).date()
        
        self.stdout.write(f'\nCreating data for {date.strftime("%B %Y")}:')
        
        # Create income data
        self._create_monthly_income(user, date)
        
        # Create expense data
        self._create_monthly_expenses(user, categories, date)

    def _create_monthly_income(self, user, date):
        # Base salary
        base_salary = 75000
        
        # Add random variation to salary
        salary = base_salary + random.randint(-2000, 2000)
        
        # Create the salary income
        Income.objects.create(
            user=user,
            amount=salary,
            date=date,
            source='salary',
            description=f'Monthly salary for {date.strftime("%B %Y")}'
        )
        
        # Add additional income sources with some randomness
        additional_income_sources = [
            ('rental', 15000, 0.7),  # 70% chance of rental income
            ('interest', 5000, 0.5),  # 50% chance of interest income
            ('freelance', 10000, 0.3),  # 30% chance of freelance income
            ('dividend', 3000, 0.4),  # 40% chance of dividend income
        ]
        
        for source, amount, probability in additional_income_sources:
            if random.random() < probability:
                # Add some variation to the amount
                varied_amount = amount + random.randint(-1000, 1000)
                varied_amount = max(varied_amount, 1000)  # Ensure positive
                
                Income.objects.create(
                    user=user,
                    amount=varied_amount,
                    date=date,
                    source=source,
                    description=f'{source.title()} income for {date.strftime("%B %Y")}'
                )
                
                self.stdout.write(f'  - {source.title()} Income: ₹{varied_amount:,.2f}')
        
        self.stdout.write(f'  - Salary Income: ₹{salary:,.2f}')

    def _create_monthly_expenses(self, user, categories, date):
        monthly_total = 0
        
        # Create expenses for each category
        for category, is_fixed, default_amount in categories:
            # For fixed expenses, use the default amount with small variation
            # For variable expenses, add more randomness and seasonal variations
            base_amount = default_amount
            
            # Add seasonal variations
            if not is_fixed:
                # Summer months (May-July) - increase entertainment, dining out, travel
                if date.month in [5, 6, 7] and category.name in ['Entertainment', 'Dining Out', 'Travel']:
                    base_amount *= 1.3
                # Winter months (Nov-Dec) - increase shopping, decrease outdoor activities
                elif date.month in [11, 12]:
                    if category.name == 'Shopping':
                        base_amount *= 1.5  # Holiday shopping
                    elif category.name in ['Entertainment', 'Transportation', 'Travel']:
                        base_amount *= 0.8
                # Spring months (Mar-Apr) - moderate increase in outdoor activities
                elif date.month in [3, 4] and category.name in ['Entertainment', 'Transportation', 'Travel']:
                    base_amount *= 1.2
                # Education expenses might be higher in certain months (e.g., new semester)
                elif date.month in [1, 7] and category.name == 'Education':
                    base_amount *= 1.5
            
            # Add random variation
            if is_fixed:
                amount = base_amount + random.randint(-1000, 1000)
            else:
                amount = base_amount + random.randint(-3000, 3000)
            
            # Ensure amount is positive and add some monthly trend
            amount = max(amount, 1000)
            # Add a small inflationary trend (0.5% increase per month)
            amount *= (1 + (date.month - 1) * 0.005)
            
            # Create the expense
            Expense.objects.create(
                user=user,
                category=category,
                amount=amount,
                date=date,
                description=f'{category.name} expense for {date.strftime("%B %Y")}'
            )
            
            monthly_total += amount
            self.stdout.write(f'  - {category.name}: ₹{amount:,.2f}')
        
        self.stdout.write(f'  Total Expenses for {date.strftime("%B %Y")}: ₹{monthly_total:,.2f}') 