# Smart Finance Tracker

A comprehensive financial management system built with Django that helps users track expenses, manage tax deductions, and monitor their financial health.

## Features

- **Expense Tracking**
  - Add, edit, and delete expenses
  - Categorize expenses
  - Track fixed vs variable expenses
  - Monthly expense summaries

- **Income Management**
  - Record multiple income sources
  - Track monthly income
  - Calculate savings rate

- **Tax Deduction Management**
  - Support for Indian tax sections (80C, 80D, etc.)
  - Track tax deductions with proof documents
  - Separate tracking for old and new tax regimes
  - Tax profile management

- **Financial Analytics**
  - Monthly financial summaries
  - Category-wise expense breakdown
  - Savings rate calculation
  - Tax savings analysis

## Technology Stack

- Python 3.12+
- Django 5.0.2
- Bootstrap 5.3.2
- SQLite (Development)
- Crispy Forms with Bootstrap 5

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/smart_finance_tracker.git
cd smart_finance_tracker
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Apply migrations:
```bash
python manage.py migrate
```

5. Load test data (optional):
```bash
python manage.py setup_test_data
```

6. Run the development server:
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to access the application.

## Test Data

The application comes with pre-configured test data that can be loaded using the `setup_test_data` management command.

### Test Users

1. **Regular User 1**
   - Username: `john_doe`
   - Email: john@example.com
   - Password: `testpass123`
   - Monthly Income: ₹75,000
   - Profile:
     - Tax Regime: Old
     - PAN Number: ABCDE####F (randomly generated)
     - Employer: Test Company Ltd.

2. **Regular User 2**
   - Username: `jane_smith`
   - Email: jane@example.com
   - Password: `testpass123`
   - Monthly Income: ₹95,000
   - Profile:
     - Tax Regime: Old
     - PAN Number: ABCDE####F (randomly generated)
     - Employer: Test Company Ltd.

### Sample Data Structure

1. **Expense Categories** (per user)
   - Rent (Fixed)
   - Groceries (Variable)
   - Transportation (Variable)
   - Entertainment (Variable)
   - Utilities (Fixed)

2. **Tax Regimes**
   - Old Regime
   - New Regime

3. **Tax Deduction Sections**
   - Section 80C
     - PPF
     - ELSS
     - Life Insurance
     - Maximum Limit: ₹1,50,000
   - Section 80D
     - Self Health Insurance
     - Family Health Insurance
     - Maximum Limit: ₹25,000

4. **Sample Records**
   - 3 months of expense records per category
   - 3 months of income records
   - Tax deductions with random verification status
   - Fixed expenses: ₹15,000 - ₹25,000 range
   - Variable expenses: ₹5,000 - ₹15,000 range

## Configuration

The application uses the following environment variables (create a `.env` file):

```
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

## Project Structure

```
smart_finance_tracker/
├── finance_tracker/        # Project settings
├── tracker/               # Main application
│   ├── migrations/       # Database migrations
│   ├── templates/       # HTML templates
│   ├── static/         # Static files
│   ├── models.py       # Database models
│   ├── views.py        # View logic
│   ├── forms.py        # Form definitions
│   └── urls.py         # URL routing
├── static/              # Global static files
├── media/              # User-uploaded files
├── requirements.txt    # Project dependencies
└── manage.py          # Django management script
```

## Usage

1. **Registration and Login**
   - Create a new account or login with existing credentials
   - Set up your user profile with income details

2. **Expense Management**
   - Add new expenses with categories
   - View and edit existing expenses
   - Track monthly spending

3. **Tax Deductions**
   - Set up your tax profile
   - Add tax deductions with supporting documents
   - Track deductions by tax sections

4. **Financial Summary**
   - View monthly and yearly summaries
   - Analyze spending patterns
   - Track savings progress

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please create an issue in the GitHub repository or contact the maintainers.

## Acknowledgments

- Django Framework
- Bootstrap
- Indian Tax Laws and Regulations 