from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from tracker.models import Category, Expense
from decimal import Decimal
from datetime import datetime
import random

class Command(BaseCommand):
    help = 'Adds fake expense data for jane_smith for January 2024'

    def handle(self, *args, **kwargs):
        self.stdout.write('Adding January 2024 expenses for jane_smith...')
        
        # Get the jane_smith user
        try:
            user = User.objects.get(username='jane_smith')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User jane_smith does not exist. Please run setup_test_data first.'))
            return
        
        # Get or create categories
        categories = self._get_or_create_categories(user)
        
        # Create expenses for January 2024
        self._create_january_expenses(user, categories)
        
        self.stdout.write(self.style.SUCCESS('Successfully added January 2024 expenses for jane_smith'))

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

    def _create_january_expenses(self, user, categories):
        # Set the date to January 2024
        january_date = datetime(2024, 1, 15).date()
        
        # Create expenses for each category
        for category, is_fixed, default_amount in categories:
            # For fixed expenses, use the default amount with small variation
            # For variable expenses, add more randomness
            if is_fixed:
                amount = default_amount + random.randint(-1000, 1000)
            else:
                amount = default_amount + random.randint(-3000, 3000)
            
            # Ensure amount is positive
            amount = max(amount, 1000)
            
            # Create the expense
            Expense.objects.create(
                user=user,
                category=category,
                amount=amount,
                date=january_date,
                description=f'{category.name} expense for January 2024'
            )
            
            self.stdout.write(f'Created {category.name} expense: ₹{amount:,.2f}') 