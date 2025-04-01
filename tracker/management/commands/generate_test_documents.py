from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tracker.models import TaxDeduction, DeductionCategory
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings
from datetime import date
import random
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import textwrap
from django.core.files.base import ContentFile

class Command(BaseCommand):
    help = 'Generates sample tax documents for testing'

    def _create_ppf_receipt(self, amount, date_str):
        """Create a PPF receipt as PDF"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 24)
        
        # Header
        c.drawString(50, 750, "State Bank of India")
        c.setFont("Helvetica", 16)
        c.drawString(50, 720, "Public Provident Fund Receipt")
        
        # Content
        c.setFont("Helvetica", 12)
        c.drawString(50, 680, f"Account Number: PPF-{random.randint(10000, 99999)}")
        c.drawString(50, 660, f"Date: {date_str}")
        c.drawString(50, 640, f"Amount Deposited: ₹{amount:,.2f}")
        c.drawString(50, 620, "Transaction Type: Cash Deposit")
        c.drawString(50, 600, "Branch: Mumbai Main Branch")
        
        # Footer
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 100, "This is a computer generated receipt")
        c.drawString(50, 80, "No signature required")
        
        c.save()
        return buffer.getvalue()

    def _create_insurance_receipt(self, amount, date_str):
        """Create a Life Insurance receipt as PDF"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Header
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, 750, "LIC of India")
        c.setFont("Helvetica", 16)
        c.drawString(50, 720, "Premium Payment Receipt")
        
        # Content
        c.setFont("Helvetica", 12)
        policy_no = f"LIC-{random.randint(100000, 999999)}"
        c.drawString(50, 680, f"Policy Number: {policy_no}")
        c.drawString(50, 660, f"Date: {date_str}")
        c.drawString(50, 640, f"Premium Amount: ₹{amount:,.2f}")
        c.drawString(50, 620, "Payment Mode: Online")
        c.drawString(50, 600, "Policy Type: Life Insurance")
        c.drawString(50, 580, "Premium Status: Paid")
        
        # Footer
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 100, "This is an electronically generated receipt")
        c.drawString(50, 80, "Valid without signature")
        
        c.save()
        return buffer.getvalue()

    def _create_health_insurance_receipt(self, amount, date_str):
        """Create a Health Insurance receipt as PDF"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Header
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, 750, "Star Health Insurance")
        c.setFont("Helvetica", 16)
        c.drawString(50, 720, "Health Insurance Premium Receipt")
        
        # Content
        c.setFont("Helvetica", 12)
        policy_no = f"STAR-HEALTH-{random.randint(10000, 99999)}"
        c.drawString(50, 680, f"Policy Number: {policy_no}")
        c.drawString(50, 660, f"Date: {date_str}")
        c.drawString(50, 640, f"Premium Amount: ₹{amount:,.2f}")
        c.drawString(50, 620, "Coverage Type: Family Floater")
        c.drawString(50, 600, "Policy Period: 1 Year")
        c.drawString(50, 580, "Payment Status: Success")
        
        # Footer
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 100, "This is a valid premium payment receipt")
        c.drawString(50, 80, "Authorized by IRDAI")
        
        c.save()
        return buffer.getvalue()

    def _create_mutual_fund_receipt(self, amount, date_str):
        """Create an ELSS Mutual Fund receipt as PDF"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Header
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, 750, "SBI Mutual Fund")
        c.setFont("Helvetica", 16)
        c.drawString(50, 720, "ELSS Investment Receipt")
        
        # Content
        c.setFont("Helvetica", 12)
        folio_no = f"ELSS-{random.randint(100000, 999999)}"
        c.drawString(50, 680, f"Folio Number: {folio_no}")
        c.drawString(50, 660, f"Date: {date_str}")
        c.drawString(50, 640, f"Investment Amount: ₹{amount:,.2f}")
        c.drawString(50, 620, "Scheme: SBI Long Term Equity Fund")
        c.drawString(50, 600, "Investment Type: ELSS (Tax Saving)")
        c.drawString(50, 580, "Lock-in Period: 3 Years")
        
        # Footer
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 100, "Mutual Fund investments are subject to market risks")
        c.drawString(50, 80, "Please read the scheme information document carefully")
        
        c.save()
        return buffer.getvalue()

    def handle(self, *args, **options):
        # Get all users
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.ERROR('No users found. Please run setup_test_data first.'))
            return

        # Create media directory if it doesn't exist
        media_root = settings.MEDIA_ROOT
        tax_proofs_dir = os.path.join(media_root, 'tax_proofs')
        os.makedirs(tax_proofs_dir, exist_ok=True)

        for user in users:
            self.stdout.write(f'Generating documents for user: {user.username}')
            
            # Get user's tax deductions
            deductions = TaxDeduction.objects.filter(user=user)
            
            for deduction in deductions:
                date_str = deduction.date_claimed.strftime('%d/%m/%Y')
                amount = float(deduction.amount)
                
                # Generate appropriate document based on category
                category_name = deduction.deduction_category.name.lower()
                section_code = deduction.deduction_category.section.section_code
                
                if section_code == '80C':
                    if 'ppf' in category_name:
                        content = self._create_ppf_receipt(amount, date_str)
                        filename = f'ppf_receipt_{user.username}.pdf'
                    elif 'insurance' in category_name:
                        content = self._create_insurance_receipt(amount, date_str)
                        filename = f'life_insurance_{user.username}.pdf'
                    elif 'elss' in category_name or 'mutual' in category_name:
                        content = self._create_mutual_fund_receipt(amount, date_str)
                        filename = f'elss_receipt_{user.username}.pdf'
                elif section_code == '80D':
                    content = self._create_health_insurance_receipt(amount, date_str)
                    filename = f'health_insurance_{user.username}.pdf'
                else:
                    continue

                # Save the document and attach to deduction
                deduction.proof_document.save(filename, ContentFile(content), save=True)
                self.stdout.write(f'Created document: {filename}')

        self.stdout.write(self.style.SUCCESS('Successfully generated test documents')) 