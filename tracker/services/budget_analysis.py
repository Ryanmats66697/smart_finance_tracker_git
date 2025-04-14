from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Avg, Sum, Count, StdDev, Min, Max
from django.utils import timezone
from ..models import Expense, Category, BudgetPrediction, BudgetRecommendation

class BudgetAnalyzer:
    def __init__(self, user):
        self.user = user
        self.today = timezone.now()
        self.start_date = self.today - timedelta(days=180)  # Last 6 months
        self.min_months_for_prediction = 3  # Minimum months of data required for predictions

    def get_category_statistics(self):
        """Calculate statistics for each expense category."""
        stats = {}
        categories = Category.objects.filter(user=self.user)
        
        for category in categories:
            expenses = Expense.objects.filter(
                user=self.user,
                category=category,
                date__range=[self.start_date, self.today]
            )
            
            if expenses.exists():
                # Get the date range of expenses
                date_range = expenses.aggregate(
                    min_date=Min('date'),
                    max_date=Max('date')
                )
                
                # Calculate the number of months between min and max date
                if date_range['min_date'] and date_range['max_date']:
                    months_diff = (date_range['max_date'].year - date_range['min_date'].year) * 12 + \
                                 (date_range['max_date'].month - date_range['min_date'].month) + 1
                else:
                    months_diff = 1  # Default to 1 if we can't calculate
                
                # Ensure we have at least 1 month of data
                months_diff = max(1, months_diff)
                
                avg = expenses.aggregate(Avg('amount'))['amount__avg']
                total = expenses.aggregate(Sum('amount'))['amount__sum']
                count = expenses.count()
                std_dev = expenses.aggregate(StdDev('amount'))['amount__stddev'] or 0
                
                stats[category.id] = {
                    'category': category,
                    'average': avg,
                    'total': total,
                    'frequency': count,
                    'std_dev': std_dev,
                    'monthly_avg': total / months_diff,  # Use actual months of data
                    'months_of_data': months_diff
                }
        
        return stats

    def analyze_spending_patterns(self):
        """Analyze spending patterns and identify trends."""
        stats = self.get_category_statistics()
        patterns = []
        
        for cat_id, data in stats.items():
            category = data['category']
            monthly_avg = data['monthly_avg']
            std_dev = data['std_dev']
            
            # Check for high variability
            if std_dev > monthly_avg * Decimal('0.3'):  # More than 30% variation
                patterns.append({
                    'category': category,
                    'type': 'high_variability',
                    'message': f'High spending variability in {category.name}'
                })
            
            # Check for high spending categories
            if monthly_avg > Decimal('10000'):  # High spending threshold
                patterns.append({
                    'category': category,
                    'type': 'high_spending',
                    'message': f'High monthly spending in {category.name}'
                })
        
        return patterns

    def generate_recommendations(self):
        """Generate budget recommendations based on spending analysis."""
        stats = self.get_category_statistics()
        patterns = self.analyze_spending_patterns()
        
        # Clear existing recommendations
        BudgetRecommendation.objects.filter(user=self.user).delete()
        
        for cat_id, data in stats.items():
            # Only generate recommendations if we have enough data
            if data['months_of_data'] < self.min_months_for_prediction:
                continue
                
            category = data['category']
            monthly_avg = data['monthly_avg']
            std_dev = data.get('std_dev', 0)
            
            # Fixed expenses check
            if category.is_fixed_expense and std_dev > monthly_avg * Decimal('0.1'):
                self._create_recommendation(
                    category=category,
                    rec_type='reduce',
                    priority='high',
                    current_amount=monthly_avg,
                    recommended_amount=monthly_avg * Decimal('0.9'),
                    reason=f"Unexpected variation in fixed expense {category.name}. Consider reviewing and optimizing."
                )
            
            # High variable expenses
            elif not category.is_fixed_expense and monthly_avg > Decimal('10000'):
                self._create_recommendation(
                    category=category,
                    rec_type='reduce',
                    priority='medium',
                    current_amount=monthly_avg,
                    recommended_amount=monthly_avg * Decimal('0.8'),
                    reason=f"High variable spending in {category.name}. Consider setting a budget limit."
                )
            
            # Saving opportunities
            elif std_dev < monthly_avg * Decimal('0.2'):
                potential_saving = monthly_avg * Decimal('0.1')
                self._create_recommendation(
                    category=category,
                    rec_type='save',
                    priority='low',
                    current_amount=monthly_avg,
                    recommended_amount=monthly_avg - potential_saving,
                    reason=f"Consistent spending in {category.name}. Potential for {potential_saving:,.2f} monthly savings."
                )

    def _create_recommendation(self, category, rec_type, priority, current_amount, recommended_amount, reason):
        """Helper method to create a budget recommendation."""
        potential_savings = current_amount - recommended_amount
        BudgetRecommendation.objects.create(
            user=self.user,
            category=category,
            recommendation_type=rec_type,
            priority=priority,
            current_amount=current_amount,
            recommended_amount=recommended_amount,
            potential_savings=potential_savings,
            reason=reason
        )

    def predict_future_expenses(self):
        """Generate predictions for future expenses."""
        stats = self.get_category_statistics()
        
        # Clear existing predictions
        BudgetPrediction.objects.filter(
            user=self.user,
            month__gt=self.today.month,
            year=self.today.year
        ).delete()
        
        for cat_id, data in stats.items():
            # Only make predictions if we have enough data
            if data['months_of_data'] < self.min_months_for_prediction:
                continue
                
            category = data['category']
            monthly_avg = data['monthly_avg']
            std_dev = data.get('std_dev', 0)
            
            # Calculate confidence score based on data consistency and amount of data
            data_confidence = min(100, (data['months_of_data'] / 6) * 100)  # Scale based on months of data
            consistency_confidence = max(0, min(100, 100 - (std_dev / monthly_avg * 100))) if monthly_avg > 0 else 0
            
            # Overall confidence is the average of data amount and consistency
            confidence = (data_confidence + consistency_confidence) / 2
            
            # Predict next 3 months
            for i in range(1, 4):
                future_month = (self.today.month + i) % 12 or 12
                future_year = self.today.year + (self.today.month + i - 1) // 12
                
                # Adjust prediction based on historical patterns
                if category.is_fixed_expense:
                    predicted_amount = monthly_avg
                else:
                    # Add slight increase for variable expenses
                    predicted_amount = monthly_avg * (1 + Decimal('0.02') * i)  # 2% increase per month
                
                BudgetPrediction.objects.create(
                    user=self.user,
                    category=category,
                    predicted_amount=predicted_amount,
                    month=future_month,
                    year=future_year,
                    confidence_score=confidence
                )