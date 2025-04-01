from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class UserProfile(models.Model):
    CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee (₹)'),
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')

    def __str__(self):
        return f"{self.user.username}'s profile"

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_fixed_expense = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.category.name} - ₹{self.amount:,.2f}"

class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    source = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username} - ₹{self.amount:,.2f} ({self.date})"

class BudgetPrediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    predicted_amount = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.IntegerField(default=1)
    year = models.IntegerField(default=2024)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Prediction confidence
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} - ₹{self.predicted_amount:,.2f} ({self.month}/{self.year})"

class BudgetRecommendation(models.Model):
    RECOMMENDATION_TYPES = [
        ('reduce', 'Reduce Spending'),
        ('maintain', 'Maintain Current'),
        ('reallocate', 'Reallocate Budget'),
        ('save', 'Saving Opportunity'),
    ]
    
    PRIORITY_LEVELS = [
        ('high', 'High Priority'),
        ('medium', 'Medium Priority'),
        ('low', 'Low Priority'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2)
    recommended_amount = models.DecimalField(max_digits=12, decimal_places=2)
    potential_savings = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    implemented = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.category.name} - {self.recommendation_type} (₹{self.potential_savings:,.2f} savings)"

    class Meta:
        ordering = ['-potential_savings']

class TaxRegime(models.Model):
    name = models.CharField(max_length=50)  # 'Old' or 'New'
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class TaxSlab(models.Model):
    regime = models.ForeignKey(TaxRegime, on_delete=models.CASCADE)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Stored as percentage
    surcharge_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cess_rate = models.DecimalField(max_digits=5, decimal_places=2, default=4.00)  # Health and Education Cess

    class Meta:
        ordering = ['regime', 'min_amount']

    def __str__(self):
        max_str = f" - ₹{self.max_amount:,.2f}" if self.max_amount else "+"
        return f"₹{self.min_amount:,.2f}{max_str} @ {self.tax_rate}%"

class DeductionSection(models.Model):
    SECTION_CHOICES = [
        ('80C', 'Section 80C - Investments & Payments'),
        ('80CCD', 'Section 80CCD - NPS Contributions'),
        ('80D', 'Section 80D - Health Insurance'),
        ('80E', 'Section 80E - Education Loan Interest'),
        ('80G', 'Section 80G - Donations'),
        ('80GG', 'Section 80GG - House Rent'),
        ('80TTA', 'Section 80TTA - Savings Interest'),
        ('80TTB', 'Section 80TTB - Senior Citizens Interest Income'),
        ('80U', 'Section 80U - Disability'),
    ]

    section_code = models.CharField(max_length=10, choices=SECTION_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    max_limit = models.DecimalField(max_digits=12, decimal_places=2)
    applicable_old_regime = models.BooleanField(default=True)
    applicable_new_regime = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.section_code} - {self.name}"

class DeductionCategory(models.Model):
    section = models.ForeignKey(DeductionSection, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField()
    max_limit = models.DecimalField(max_digits=12, decimal_places=2)
    requires_proof = models.BooleanField(default=True)
    proof_description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Deduction Categories"

    def __str__(self):
        return f"{self.section.section_code} - {self.name}"

class TaxDeduction(models.Model):
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    deduction_category = models.ForeignKey(DeductionCategory, on_delete=models.CASCADE, related_name='deductions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    fiscal_year = models.CharField(max_length=7)  # Format: 2023-24
    date_claimed = models.DateField()
    proof_document = models.FileField(upload_to='tax_proofs/', null=True, blank=True)
    verification_status = models.CharField(max_length=10, choices=VERIFICATION_STATUS, default='pending')
    verification_notes = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.deduction_category.name} - ₹{self.amount:,.2f}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount > self.deduction_category.max_limit:
            raise ValidationError(f'Amount exceeds maximum limit of ₹{self.deduction_category.max_limit:,.2f} for this category')

class UserTaxProfile(models.Model):
    REGIME_CHOICES = [
        ('old', 'Old Regime'),
        ('new', 'New Regime'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    pan_number = models.CharField(max_length=10)
    tax_regime = models.CharField(max_length=3, choices=REGIME_CHOICES, default='old')
    is_senior_citizen = models.BooleanField(default=False)
    is_super_senior_citizen = models.BooleanField(default=False)
    employer_name = models.CharField(max_length=200, blank=True)
    form_16_document = models.FileField(upload_to='form16/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Tax Profile"

    def save(self, *args, **kwargs):
        # Auto-calculate senior citizen status based on age
        from datetime import date
        today = date.today()
        age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        self.is_senior_citizen = age >= 60
        self.is_super_senior_citizen = age >= 80
        super().save(*args, **kwargs)
