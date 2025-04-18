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
    TaxDeduction, DeductionCategory, UserTaxProfile, DeductionSection,
    BudgetRecommendation
)
from .forms import (
    ExpenseForm, CategoryForm, UserRegistrationForm, UserProfileForm,
    IncomeForm, TaxDeductionForm, UserTaxProfileForm
)
from .services.budget_analysis import BudgetAnalyzer
from django.http import JsonResponse
import json

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

    # Run budget analysis and get recommendations
    analyzer = BudgetAnalyzer(request.user)
    analyzer.predict_future_expenses()
    analyzer.generate_recommendations()

    # Get predictions and recommendations
    predictions = BudgetPrediction.objects.filter(
        user=request.user,
        month__gt=today.month,
        year=today.year
    ).select_related('category').order_by('year', 'month')

    recommendations = BudgetRecommendation.objects.filter(
        user=request.user,
        implemented=False
    ).select_related('category').order_by('priority', '-potential_savings')[:5]  # Top 5 recommendations

    # Prepare prediction data for charts
    prediction_months = []
    predicted_amounts = []
    actual_amounts = []
    
    # Last 6 months actual data
    for i in range(5, -1, -1):
        date = today - timedelta(days=i*30)
        month_expenses = Expense.objects.filter(
            user=request.user,
            date__year=date.year,
            date__month=date.month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        actual_amounts.append(float(month_expenses))
        prediction_months.append(date.strftime('%B %Y'))

    # Next 3 months predictions
    for prediction in predictions:
        month_name = calendar.month_name[prediction.month]
        prediction_months.append(f"{month_name} {prediction.year}")
        predicted_amounts.append(float(prediction.predicted_amount))

    context = {
        'monthly_income': monthly_income,
        'total_expenses': total_expenses,
        'savings_rate': round(savings_rate, 1),
        'category_totals': category_totals,
        'prediction_months': prediction_months,
        'predicted_amounts': predicted_amounts,
        'actual_months': prediction_months[:6],
        'actual_amounts': actual_amounts,
        'recommendations': recommendations,
        'predictions': predictions,
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, 'Expense added successfully.')
            return redirect('tracker:dashboard')
    else:
        form = ExpenseForm(user=request.user)
    
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
            
            # Update user's monthly income in UserProfile if it's a salary entry
            try:
                profile = UserProfile.objects.get(user=request.user)
                if income.source == 'salary':  # If it's a salary entry
                    profile.monthly_income = income.amount
                    profile.save()
            except UserProfile.DoesNotExist:
                pass
                
            income.save()
            messages.success(request, 'Income added successfully.')
            return redirect('tracker:dashboard')
    else:
        # Set default date to today
        initial_data = {'date': timezone.now().date()}
        form = IncomeForm(initial=initial_data)
    
    return render(request, 'tracker/add_income.html', {'form': form})

@login_required
def financial_summary(request):
    """View for displaying financial summary including income and expenses for the last 12 months."""
    # Get the date range for the last 12 months
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=365)
    
    # Get expenses for the last 12 months
    expenses = Expense.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    ).select_related('category')
    
    # Get income for the last 12 months
    income = Income.objects.filter(
        user=request.user,
        date__range=[start_date, end_date]
    )
    
    # Initialize monthly totals dictionary
    monthly_totals = {}
    
    # Process expenses
    for expense in expenses:
        month_key = expense.date.strftime('%B %Y')
        if month_key not in monthly_totals:
            monthly_totals[month_key] = {
                'total_expenses': 0,
                'total_income': 0,
                'net_income': 0,
                'categories': {}
            }
        
        monthly_totals[month_key]['total_expenses'] += expense.amount
        category_name = expense.category.name
        if category_name not in monthly_totals[month_key]['categories']:
            monthly_totals[month_key]['categories'][category_name] = 0
        monthly_totals[month_key]['categories'][category_name] += expense.amount
    
    # Process income
    for income_item in income:
        month_key = income_item.date.strftime('%B %Y')
        if month_key not in monthly_totals:
            monthly_totals[month_key] = {
                'total_expenses': 0,
                'total_income': 0,
                'net_income': 0,
                'categories': {}
            }
        
        monthly_totals[month_key]['total_income'] += income_item.amount
    
    # Calculate net income for each month
    for month_data in monthly_totals.values():
        month_data['net_income'] = month_data['total_income'] - month_data['total_expenses']
    
    # Sort months chronologically
    sorted_months = sorted(monthly_totals.keys(), 
                         key=lambda x: datetime.strptime(x, '%B %Y'))
    
    # Prepare data for the line graph
    months = []
    expense_data = []
    income_data = []
    
    for month in sorted_months:
        months.append(month)
        expense_data.append(float(monthly_totals[month]['total_expenses']))
        income_data.append(float(monthly_totals[month]['total_income']))
    
    # Convert to JSON for JavaScript
    months_json = json.dumps(months)
    expense_data_json = json.dumps(expense_data)
    income_data_json = json.dumps(income_data)
    
    context = {
        'monthly_totals': monthly_totals,
        'months': months_json,
        'expense_data': expense_data_json,
        'income_data': income_data_json,
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

@login_required
def get_monthly_data(request):
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    # Get expenses for the selected month
    expenses = Expense.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    ).select_related('category')
    
    # Calculate total expenses
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Get income for the selected month
    monthly_income = Income.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Calculate savings rate
    if monthly_income > 0:
        savings_rate = ((monthly_income - total_expenses) / monthly_income) * 100
    else:
        savings_rate = Decimal('0')
    
    # Get category totals
    categories = Category.objects.filter(user=request.user)
    category_totals = []
    for category in categories:
        total = expenses.filter(category=category).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        if total > 0:
            category_totals.append({
                'name': category.name,
                'total': float(total),
                'percentage': float((total / total_expenses * 100) if total_expenses > 0 else Decimal('0'))
            })
    
    return JsonResponse({
        'total_expenses': float(total_expenses),
        'monthly_income': float(monthly_income),
        'savings_rate': float(savings_rate),
        'category_totals': category_totals
    })
