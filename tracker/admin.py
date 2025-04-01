from django.contrib import admin
from .models import (
    UserProfile,
    Category,
    Expense,
    Income,
    BudgetPrediction,
    TaxRegime,
    TaxSlab,
    DeductionSection,
    DeductionCategory,
    TaxDeduction,
    UserTaxProfile
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'monthly_income', 'currency')
    search_fields = ('user__username', 'currency')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_fixed_expense')
    list_filter = ('is_fixed_expense',)
    search_fields = ('name', 'user__username')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'amount', 'date', 'description')
    list_filter = ('category', 'date')
    search_fields = ('user__username', 'description')
    date_hierarchy = 'date'

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'date', 'source')
    list_filter = ('date',)
    search_fields = ('user__username', 'source')
    date_hierarchy = 'date'

@admin.register(BudgetPrediction)
class BudgetPredictionAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'predicted_amount', 'month', 'year')
    list_filter = ('month', 'year')
    search_fields = ('user__username',)

@admin.register(TaxRegime)
class TaxRegimeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(TaxSlab)
class TaxSlabAdmin(admin.ModelAdmin):
    list_display = ('regime', 'min_amount', 'max_amount', 'tax_rate', 'surcharge_rate', 'cess_rate')
    list_filter = ('regime',)
    search_fields = ('regime__name',)

@admin.register(DeductionSection)
class DeductionSectionAdmin(admin.ModelAdmin):
    list_display = ('section_code', 'name', 'max_limit', 'applicable_old_regime', 'applicable_new_regime')
    list_filter = ('applicable_old_regime', 'applicable_new_regime')
    search_fields = ('section_code', 'name')

@admin.register(DeductionCategory)
class DeductionCategoryAdmin(admin.ModelAdmin):
    list_display = ('section', 'name', 'max_limit', 'requires_proof')
    list_filter = ('requires_proof', 'section')
    search_fields = ('name', 'section__section_code')

@admin.register(TaxDeduction)
class TaxDeductionAdmin(admin.ModelAdmin):
    list_display = ('user', 'deduction_category', 'amount', 'fiscal_year', 'verification_status')
    list_filter = ('verification_status', 'fiscal_year')
    search_fields = ('user__username', 'deduction_category__name')
    date_hierarchy = 'date_claimed'

@admin.register(UserTaxProfile)
class UserTaxProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'pan_number', 'tax_regime', 'is_senior_citizen', 'is_super_senior_citizen')
    list_filter = ('tax_regime', 'is_senior_citizen', 'is_super_senior_citizen')
    search_fields = ('user__username', 'pan_number', 'employer_name')
