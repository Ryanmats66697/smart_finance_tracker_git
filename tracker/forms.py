from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    Category, Expense, UserProfile, Income,
    TaxDeduction, UserTaxProfile
)

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['monthly_income', 'currency']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_fixed_expense']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'amount': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
        # Set default date to today if no date is provided
        if not self.instance.pk and not self.data.get('date'):
            self.fields['date'].initial = timezone.now().date()

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['source', 'amount', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
        }
        help_texts = {
            'source': 'Select the type of income you\'re adding.',
            'description': 'Add any additional details about this income.',
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

class TaxDeductionForm(forms.ModelForm):
    class Meta:
        model = TaxDeduction
        fields = ['deduction_category', 'amount', 'fiscal_year', 'date_claimed', 'proof_document']
        widgets = {
            'date_claimed': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            try:
                tax_profile = UserTaxProfile.objects.get(user=user)
                if tax_profile.tax_regime == 'new':
                    self.fields['deduction_category'].queryset = self.fields['deduction_category'].queryset.filter(
                        section__applicable_new_regime=True
                    )
                else:
                    self.fields['deduction_category'].queryset = self.fields['deduction_category'].queryset.filter(
                        section__applicable_old_regime=True
                    )
            except UserTaxProfile.DoesNotExist:
                pass

class UserTaxProfileForm(forms.ModelForm):
    class Meta:
        model = UserTaxProfile
        fields = ['date_of_birth', 'pan_number', 'tax_regime', 'employer_name', 'form_16_document']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        } 