from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from tracker.models import Category, Expense
from decimal import Decimal
from datetime import datetime
import random

class Command(BaseCommand):
    help = 'Adds fake expense data for jane_smith from February to December 2024'

    def handle(self, *args, **kwargs):
        self.stdout.write('Adding expenses for February-December 2024 for jane_smith...')
        
        # Get the jane_smith user
        try:
            user = User.objects.get(username='jane_smith')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User jane_smith does not exist. Please run setup_test_data first.'))
            return
        
        # Get or create categories
        categories = self._get_or_create_categories(user)
        
        # Create expenses for Feb-Dec 2024
        for month in range(2, 13):  # 2 = February, 12 = December
            self._create_monthly_expenses(user, categories, month)
        
        self.stdout.write(self.style.SUCCESS('Successfully added expenses for February-December 2024'))

    def _get_or_create_categories(self, user):
        categories = []
        category_data = [
            ('Rent', True, 20000),
            ('Groceries', False, 12000),
            ('Transportation', False, 8000),
            ('Entertainment', False, 5000),
            ('Utilities', True, 15000),
            ('Shopping', False, 10000),
            ('Dining Out', False, 7000),
            ('Healthcare', False, 3000)
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

    def _create_monthly_expenses(self, user, categories, month):
        # Set the date to the 15th of each month in 2024
        date = datetime(2024, month, 15).date()
        
        self.stdout.write(f'\nCreating expenses for {date.strftime("%B %Y")}:')
        monthly_total = 0
        
        # Create expenses for each category
        for category, is_fixed, default_amount in categories:
            # For fixed expenses, use the default amount with small variation
            # For variable expenses, add more randomness and seasonal variations
            base_amount = default_amount
            
            # Add seasonal variations
            if not is_fixed:
                # Summer months (May-July) - increase entertainment, dining out
                if month in [5, 6, 7] and category.name in ['Entertainment', 'Dining Out']:
                    base_amount *= 1.3
                # Winter months (Nov-Dec) - increase shopping, decrease outdoor activities
                elif month in [11, 12]:
                    if category.name == 'Shopping':
                        base_amount *= 1.5  # Holiday shopping
                    elif category.name in ['Entertainment', 'Transportation']:
                        base_amount *= 0.8
                # Spring months (Mar-Apr) - moderate increase in outdoor activities
                elif month in [3, 4] and category.name in ['Entertainment', 'Transportation']:
                    base_amount *= 1.2
            
            # Add random variation
            if is_fixed:
                amount = base_amount + random.randint(-1000, 1000)
            else:
                amount = base_amount + random.randint(-3000, 3000)
            
            # Ensure amount is positive and add some monthly trend
            amount = max(amount, 1000)
            # Add a small inflationary trend (0.5% increase per month)
            amount *= (1 + (month - 1) * 0.005)
            
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
        
        self.stdout.write(f'  Total for {date.strftime("%B %Y")}: ₹{monthly_total:,.2f}') 