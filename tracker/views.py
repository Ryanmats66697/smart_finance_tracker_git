from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
import random
from decimal import Decimal
from .models import (
    Category, Expense, BudgetPrediction, UserProfile, Income,
    TaxDeduction, DeductionCategory, UserTaxProfile, DeductionSection
)
from .forms import (
    ExpenseForm, CategoryForm, UserRegistrationForm, UserProfileForm,
    IncomeForm, TaxDeductionForm, UserTaxProfileForm
)

@login_required
def dashboard(request):
    # Get current month's expenses
    today = timezone.now()
    current_month_expenses = Expense.objects.filter(
        user=request.user,
        date__year=today.year,
        date__month=today.month
    ).select_related('category')

    # Calculate total expenses
    total_expenses = current_month_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Get user's income
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        monthly_income = user_profile.monthly_income
    except UserProfile.DoesNotExist:
        monthly_income = Decimal('0')

    # Calculate savings rate
    if monthly_income > 0:
        savings_rate = ((monthly_income - total_expenses) / monthly_income) * 100
    else:
        savings_rate = Decimal('0')

    # Get expense categories and their totals
    categories = Category.objects.filter(user=request.user)
    category_totals = []
    for category in categories:
        total = current_month_expenses.filter(category=category).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        if total > 0:  # Only include categories with expenses
            category_totals.append({
                'name': category.name,
                'total': total,
                'percentage': (total / total_expenses * 100) if total_expenses > 0 else Decimal('0')
            })

    # Get tax deductions
    tax_deductions = TaxDeduction.objects.filter(
        user=request.user,
        fiscal_year=f"{today.year}-{str(today.year + 1)[2:]}"
    ).select_related('deduction_category')
    total_deductions = tax_deductions.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Get historical data for predictions
    last_6_months = []
    actual_amounts = []
    prediction_months = []
    predicted_amounts = []
    
    for i in range(5, -1, -1):  # Last 6 months
        date = today - timedelta(days=i*30)
        month_expenses = Expense.objects.filter(
            user=request.user,
            date__year=date.year,
            date__month=date.month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        last_6_months.append(month_expenses)
        actual_amounts.append(float(month_expenses))  # Convert to float for JSON serialization
        prediction_months.append(date.strftime('%B %Y'))

    # Calculate predictions for next 3 months
    for i in range(1, 4):
        date = today + timedelta(days=i*30)
        prediction_months.append(date.strftime('%B %Y'))
        
        # Simple prediction based on average and trend
        avg_expense = sum(last_6_months) / Decimal('6')
        trend = (last_6_months[-1] - last_6_months[0]) / Decimal('5')  # Change per month
        
        # Predict next month's expense
        prediction = avg_expense + (trend * Decimal(str(i)))
        
        # Add some randomness for variable expenses (convert to Decimal)
        random_factor = Decimal(str(1 + random.uniform(-0.05, 0.05)))
        prediction = prediction * random_factor
        
        predicted_amounts.append(float(round(prediction, 2)))  # Convert to float for JSON serialization

    context = {
        'monthly_income': monthly_income,
        'total_expenses': total_expenses,
        'savings_rate': round(savings_rate, 1),
        'category_totals': category_totals,
        'tax_deductions': tax_deductions,
        'total_deductions': total_deductions,
        'prediction_months': prediction_months,
        'predicted_amounts': predicted_amounts,
        'actual_months': prediction_months[:6],
        'actual_amounts': actual_amounts,
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, 'Expense added successfully.')
            return redirect('tracker:dashboard')
    else:
        form = ExpenseForm()
    
    return render(request, 'tracker/add_expense.html', {'form': form})

@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Category added successfully.')
            return redirect('tracker:dashboard')
    else:
        form = CategoryForm()
    
    return render(request, 'tracker/add_category.html', {'form': form})

@login_required
def add_income(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            messages.success(request, 'Income added successfully.')
            return redirect('tracker:dashboard')
    else:
        form = IncomeForm()
    
    return render(request, 'tracker/add_income.html', {'form': form})

@login_required
def financial_summary(request):
    # Get expenses for the last 12 months
    end_date = timezone.now()
    start_date = end_date - timedelta(days=365)
    
    expenses = Expense.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).select_related('category')
    
    # Calculate monthly totals
    monthly_totals = {}
    for expense in expenses:
        month_key = expense.date.strftime('%Y-%m')
        if month_key not in monthly_totals:
            monthly_totals[month_key] = {'total': 0, 'categories': {}}
        monthly_totals[month_key]['total'] += expense.amount
        
        # Track category totals
        cat_name = expense.category.name
        if cat_name not in monthly_totals[month_key]['categories']:
            monthly_totals[month_key]['categories'][cat_name] = 0
        monthly_totals[month_key]['categories'][cat_name] += expense.amount
    
    context = {
        'monthly_totals': monthly_totals,
    }
    return render(request, 'tracker/financial_summary.html', context)

@login_required
def tax_deductions(request):
    if request.method == 'POST':
        form = TaxDeductionForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            deduction = form.save(commit=False)
            deduction.user = request.user
            deduction.save()
            messages.success(request, 'Tax deduction added successfully.')
            return redirect('tracker:tax_deductions')
    else:
        form = TaxDeductionForm(user=request.user)

    deductions = TaxDeduction.objects.filter(user=request.user).order_by('-date_claimed')
    sections = DeductionSection.objects.all()

    try:
        tax_profile = UserTaxProfile.objects.get(user=request.user)
    except UserTaxProfile.DoesNotExist:
        tax_profile = None

    context = {
        'form': form,
        'deductions': deductions,
        'sections': sections,
        'tax_profile': tax_profile,
    }
    return render(request, 'tracker/tax_deductions.html', context)

@login_required
def edit_tax_deduction(request, deduction_id):
    deduction = get_object_or_404(TaxDeduction, id=deduction_id, user=request.user)
    
    if request.method == 'POST':
        form = TaxDeductionForm(request.POST, request.FILES, instance=deduction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tax deduction updated successfully.')
            return redirect('tracker:tax_deductions')
    else:
        form = TaxDeductionForm(instance=deduction, user=request.user)
    
    return render(request, 'tracker/edit_tax_deduction.html', {'form': form, 'deduction': deduction})

@login_required
def delete_tax_deduction(request, deduction_id):
    deduction = get_object_or_404(TaxDeduction, id=deduction_id, user=request.user)
    
    if request.method == 'POST':
        deduction.delete()
        messages.success(request, 'Tax deduction deleted successfully.')
        return redirect('tracker:tax_deductions')
    
    return render(request, 'tracker/delete_tax_deduction.html', {'deduction': deduction})

@login_required
def tax_profile(request):
    try:
        tax_profile = UserTaxProfile.objects.get(user=request.user)
    except UserTaxProfile.DoesNotExist:
        tax_profile = None

    if request.method == 'POST':
        form = UserTaxProfileForm(request.POST, request.FILES, instance=tax_profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Tax profile updated successfully.')
            return redirect('tracker:tax_profile')
    else:
        form = UserTaxProfileForm(instance=tax_profile)

    return render(request, 'tracker/tax_profile.html', {'form': form, 'tax_profile': tax_profile})

@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully.')
            return redirect('tracker:dashboard')
    else:
        form = ExpenseForm(instance=expense)
    
    return render(request, 'tracker/edit_expense.html', {'form': form, 'expense': expense})

@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully.')
        return redirect('tracker:dashboard')
    
    return render(request, 'tracker/delete_expense.html', {'expense': expense})

@login_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('tracker:dashboard')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'tracker/edit_category.html', {'form': form, 'category': category})

@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        return redirect('tracker:dashboard')
    
    return render(request, 'tracker/delete_category.html', {'category': category})

@login_required
def edit_income(request, income_id):
    income = get_object_or_404(Income, id=income_id, user=request.user)
    
    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, 'Income updated successfully.')
            return redirect('tracker:dashboard')
    else:
        form = IncomeForm(instance=income)
    
    return render(request, 'tracker/edit_income.html', {'form': form, 'income': income})

@login_required
def delete_income(request, income_id):
    income = get_object_or_404(Income, id=income_id, user=request.user)
    
    if request.method == 'POST':
        income.delete()
        messages.success(request, 'Income deleted successfully.')
        return redirect('tracker:dashboard')
    
    return render(request, 'tracker/delete_income.html', {'income': income})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            messages.success(request, 'Account created successfully. You can now login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'tracker/register.html', {'form': form})
