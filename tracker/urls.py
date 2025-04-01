from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('financial-summary/', views.financial_summary, name='financial_summary'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('add-category/', views.add_category, name='add_category'),
    path('add-income/', views.add_income, name='add_income'),
    path('tax-deductions/', views.tax_deductions, name='tax_deductions'),
    path('tax-profile/', views.tax_profile, name='tax_profile'),
    path('expense/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('expense/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),
    path('category/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('category/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    path('income/<int:income_id>/edit/', views.edit_income, name='edit_income'),
    path('income/<int:income_id>/delete/', views.delete_income, name='delete_income'),
    path('tax-deductions/<int:deduction_id>/edit/', views.edit_tax_deduction, name='edit_tax_deduction'),
    path('tax-deductions/<int:deduction_id>/delete/', views.delete_tax_deduction, name='delete_tax_deduction'),
] 