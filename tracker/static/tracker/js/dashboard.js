document.addEventListener('DOMContentLoaded', function() {
    // Initialize date variables
    let currentDate = new Date();
    let selectedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    
    // Get DOM elements
    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    const currentMonthDisplay = document.getElementById('currentMonthDisplay');
    const totalIncomeElement = document.getElementById('total-income');
    const totalExpensesElement = document.getElementById('total-expenses');
    const savingsRateElement = document.getElementById('savings-rate');
    
    // Update month display
    function updateMonthDisplay() {
        const options = { month: 'long', year: 'numeric' };
        currentMonthDisplay.textContent = selectedDate.toLocaleDateString('en-US', options);
    }
    
    // Format currency
    function formatCurrency(amount) {
        return '₹' + parseFloat(amount).toFixed(2);
    }
    
    // Update financial overview
    function updateFinancialOverview() {
        const year = selectedDate.getFullYear();
        const month = selectedDate.getMonth() + 1;
        
        fetch(`/tracker/monthly-data/?year=${year}&month=${month}`)
            .then(response => response.json())
            .then(data => {
                // Update Total Income
                if (totalIncomeElement) {
                    totalIncomeElement.textContent = formatCurrency(data.monthly_income);
                }
                
                // Update Total Expenses
                if (totalExpensesElement) {
                    totalExpensesElement.textContent = formatCurrency(data.total_expenses);
                }
                
                // Update Savings Rate
                if (savingsRateElement) {
                    savingsRateElement.textContent = data.savings_rate.toFixed(1) + '%';
                }
                
                // Update expense chart and table
                updateExpenseChart(data.category_totals);
            })
            .catch(error => console.error('Error fetching monthly data:', error));
    }
    
    // Update expense chart
    function updateExpenseChart(categoryTotals) {
        const ctx = document.getElementById('expense-chart');
        if (!ctx) return;
        
        // Destroy existing chart if it exists
        if (window.expenseChart) {
            window.expenseChart.destroy();
        }
        
        // Prepare data for the chart
        const labels = categoryTotals.map(cat => cat.name);
        const data = categoryTotals.map(cat => cat.total);
        const backgroundColors = categoryTotals.map((_, index) => {
            const hue = (index * 137.508) % 360; // Golden angle approximation
            return `hsl(${hue}, 70%, 50%)`;
        });
        
        // Create new chart
        window.expenseChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
        
        // Update table
        const tbody = document.querySelector('.table tbody');
        if (tbody) {
            tbody.innerHTML = categoryTotals.map(cat => `
                <tr>
                    <td>${cat.name}</td>
                    <td>${formatCurrency(cat.total)}</td>
                    <td>${cat.percentage.toFixed(1)}%</td>
                </tr>
            `).join('') || '<tr><td colspan="3" class="text-center">No expenses recorded this month.</td></tr>';
        }
    }
    
    // Event listeners for month navigation
    prevMonthBtn.addEventListener('click', function() {
        selectedDate.setMonth(selectedDate.getMonth() - 1);
        updateMonthDisplay();
        updateFinancialOverview();
    });
    
    nextMonthBtn.addEventListener('click', function() {
        selectedDate.setMonth(selectedDate.getMonth() + 1);
        updateMonthDisplay();
        updateFinancialOverview();
    });
    
    // Initial updates
    updateMonthDisplay();
    updateFinancialOverview();
}); 