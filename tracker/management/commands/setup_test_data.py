from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from tracker.models import (
    UserProfile, Category, Expense, Income, TaxDeduction,
    DeductionSection, DeductionCategory, UserTaxProfile, TaxRegime
)
from decimal import Decimal
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Populates the database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating test data...')
        
        # Create test users
        test_users = self._create_test_users()
        
        # Create tax regimes
        tax_regimes = self._create_tax_regimes()
        
        # Create deduction sections
        deduction_sections = self._create_deduction_sections()
        
        # Create categories and expenses for each user
        for user in test_users:
            self._create_user_data(user, deduction_sections)
        
        self.stdout.write(self.style.SUCCESS('Successfully created test data'))

    def _create_test_users(self):
        users = []
        test_users_data = [
            {
                'username': 'john_doe',
                'email': 'john@example.com',
                'password': 'testpass123',
                'income': 75000,
                'currency': 'INR'
            },
            {
                'username': 'jane_smith',
                'email': 'jane@example.com',
                'password': 'testpass123',
                'income': 95000,
                'currency': 'INR'
            }
        ]

        for user_data in test_users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                email=user_data['email']
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                UserProfile.objects.create(
                    user=user,
                    monthly_income=user_data['income'],
                    currency=user_data['currency']
                )
                # Create tax profile
                UserTaxProfile.objects.create(
                    user=user,
                    date_of_birth=timezone.now().date() - timedelta(days=365*30),
                    pan_number=f'ABCDE{random.randint(1000, 9999)}F',
                    tax_regime='old',
                    employer_name='Test Company Ltd.'
                )
            users.append(user)
        return users

    def _create_tax_regimes(self):
        regimes = []
        for name in ['Old', 'New']:
            regime, _ = TaxRegime.objects.get_or_create(
                name=name,
                defaults={
                    'description': f'{name} Tax Regime for FY 2024-25',
                    'is_active': True
                }
            )
            regimes.append(regime)
        return regimes

    def _create_deduction_sections(self):
        sections = []
        section_data = [
            {
                'code': '80C',
                'name': 'Investments & Payments',
                'limit': 150000,
                'old': True,
                'new': False
            },
            {
                'code': '80D',
                'name': 'Health Insurance',
                'limit': 25000,
                'old': True,
                'new': False
            }
        ]

        for data in section_data:
            section, _ = DeductionSection.objects.get_or_create(
                section_code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': f'Tax deduction under section {data["code"]}',
                    'max_limit': data['limit'],
                    'applicable_old_regime': data['old'],
                    'applicable_new_regime': data['new']
                }
            )
            
            # Create deduction categories
            if data['code'] == '80C':
                categories = ['PPF', 'ELSS', 'Life Insurance']
            else:
                categories = ['Self Health Insurance', 'Family Health Insurance']

            for cat_name in categories:
                DeductionCategory.objects.get_or_create(
                    section=section,
                    name=cat_name,
                    defaults={
                        'description': f'{cat_name} under section {data["code"]}',
                        'max_limit': data['limit'],
                        'requires_proof': True
                    }
                )
            
            sections.append(section)
        return sections

    def _create_user_data(self, user, deduction_sections):
        # Create expense categories
        categories = [
            ('Rent', True),
            ('Groceries', False),
            ('Transportation', False),
            ('Entertainment', False),
            ('Utilities', True)
        ]

        for name, is_fixed in categories:
            category, _ = Category.objects.get_or_create(
                name=name,
                user=user,
                defaults={
                    'description': f'{name} expenses',
                    'is_fixed_expense': is_fixed
                }
            )

            # Create expenses for the last 3 months
            for i in range(3):
                date = timezone.now().date() - timedelta(days=30*i)
                if is_fixed:
                    amount = random.randint(15000, 25000)
                else:
                    amount = random.randint(5000, 15000)
                
                Expense.objects.create(
                    user=user,
                    category=category,
                    amount=amount,
                    date=date,
                    description=f'{name} expense for {date.strftime("%B %Y")}'
                )

        # Create income records
        for i in range(3):
            date = timezone.now().date() - timedelta(days=30*i)
            Income.objects.create(
                user=user,
                amount=user.userprofile.monthly_income,
                date=date,
                source='Salary',
                description=f'Monthly salary for {date.strftime("%B %Y")}'
            )

        # Create tax deductions
        deduction_cats = DeductionCategory.objects.filter(
            section__in=deduction_sections
        )
        
        for cat in deduction_cats:
            amount = random.randint(10000, int(cat.max_limit))
            TaxDeduction.objects.create(
                user=user,
                deduction_category=cat,
                amount=amount,
                fiscal_year='2024-25',
                date_claimed=timezone.now().date(),
                verification_status=random.choice(['pending', 'verified', 'rejected'])
            ) 