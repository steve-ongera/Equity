# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from decimal import Decimal
import uuid
from datetime import datetime, timedelta
import secrets
import string

# Custom User Model
class User(AbstractUser):
    USER_TYPES = (
        ('customer', 'Customer'),
        ('agent', 'Bank Agent'),
        ('staff', 'Bank Staff'),
        ('admin', 'Administrator'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='customer')
    phone_number = models.CharField(
        max_length=15, 
        unique=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', message="Enter a valid phone number")]
    )
    national_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    occupation = models.CharField(max_length=100, blank=True)
    employer = models.CharField(max_length=200, blank=True)
    monthly_income = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    kyc_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('verified', 'Verified'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    is_active_customer = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Limits for {self.national_id}"

# KYC Documents
class KYCDocument(models.Model):
    DOCUMENT_TYPES = (
        ('national_id', 'National ID'),
        ('passport', 'Passport'),
        ('driving_license', 'Driving License'),
        ('utility_bill', 'Utility Bill'),
        ('bank_statement', 'Bank Statement'),
        ('payslip', 'Payslip'),
        ('business_permit', 'Business Permit'),
        ('tax_certificate', 'Tax Certificate'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='kyc_documents/')
    document_number = models.CharField(max_length=50, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_document_type_display()}"
    


# Branch Model
class Branch(models.Model):
    name = models.CharField(max_length=200)
    branch_code = models.CharField(max_length=10, unique=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_branches')
    is_active = models.BooleanField(default=True)
    opening_time = models.TimeField(default='08:00:00')
    closing_time = models.TimeField(default='17:00:00')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.branch_code}"

# Bank Agent Model
class BankAgent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    agent_code = models.CharField(max_length=15, unique=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='agents')
    business_name = models.CharField(max_length=200)
    business_address = models.TextField()
    business_phone = models.CharField(max_length=15)
    license_number = models.CharField(max_length=50)
    daily_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('500000.00'))
    monthly_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('10000000.00'))
    current_daily_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    current_monthly_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.business_name} - {self.agent_code}"

# Account Types
class AccountType(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Savings", "Current", "Fixed Deposit"
    code = models.CharField(max_length=10, unique=True)
    minimum_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    monthly_maintenance_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    interest_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.00'))
    withdrawal_limit_daily = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('100000.00'))
    withdrawal_limit_monthly = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('1000000.00'))
    requires_maintaining_balance = models.BooleanField(default=True)
    allows_overdraft = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# Bank Account Model
class BankAccount(models.Model):
    ACCOUNT_STATUS = (
        ('active', 'Active'),
        ('dormant', 'Dormant'),
        ('frozen', 'Frozen'),
        ('closed', 'Closed'),
    )
    
    account_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    created_by_agent = models.ForeignKey(BankAgent, on_delete=models.SET_NULL, null=True, blank=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    available_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=10, choices=ACCOUNT_STATUS, default='active')
    pin_hash = models.CharField(max_length=255, blank=True)  # For ATM/transaction PIN
    is_primary = models.BooleanField(default=False)
    overdraft_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    last_transaction_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = self.generate_account_number()
        super().save(*args, **kwargs)

    def generate_account_number(self):
        # Generate account number based on branch code and sequential number
        import random
        return f"{self.branch.branch_code}{random.randint(1000000, 9999999)}"

    def __str__(self):
        return f"{self.account_number} - {self.customer.username}"


# ATM Machine Model
class ATMMachine(models.Model):
    ATM_STATUS = (
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('maintenance', 'Under Maintenance'),
        ('out_of_cash', 'Out of Cash'),
    )
    
    atm_id = models.CharField(max_length=20, unique=True)
    location_name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='atms')
    status = models.CharField(max_length=15, choices=ATM_STATUS, default='online')
    cash_available = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('2000000.00'))
    max_cash_capacity = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('5000000.00'))
    daily_withdrawal_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('40000.00'))
    single_withdrawal_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('20000.00'))
    supports_deposit = models.BooleanField(default=False)
    supports_cardless = models.BooleanField(default=True)
    last_maintenance = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.atm_id} - {self.location_name}"



# Transaction Model
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('bill_payment', 'Bill Payment'),
        ('airtime_purchase', 'Airtime Purchase'),
        ('loan_disbursement', 'Loan Disbursement'),
        ('loan_repayment', 'Loan Repayment'),
        ('fee_charge', 'Fee Charge'),
        ('interest_credit', 'Interest Credit'),
        ('reversal', 'Reversal'),
    )
    
    TRANSACTION_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('reversed', 'Reversed'),
    )
    
    CHANNELS = (
        ('atm', 'ATM'),
        ('mobile', 'Mobile Banking'),
        ('internet', 'Internet Banking'),
        ('ussd', 'USSD'),
        ('agent', 'Agent Banking'),
        ('branch', 'Branch'),
        ('pos', 'Point of Sale'),
    )
    
    transaction_id = models.CharField(max_length=30, unique=True, editable=False)
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_before = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    channel = models.CharField(max_length=10, choices=CHANNELS)
    reference_number = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=15, choices=TRANSACTION_STATUS, default='pending')
    
    # For transfers
    beneficiary_account = models.ForeignKey(
        BankAccount, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='received_transactions'
    )
    beneficiary_name = models.CharField(max_length=200, blank=True)
    beneficiary_bank = models.CharField(max_length=200, blank=True)
    
    # Location/Source information
    atm_machine = models.ForeignKey(ATMMachine, on_delete=models.SET_NULL, null=True, blank=True)
    agent = models.ForeignKey(BankAgent, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Device/Session information
    device_info = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        super().save(*args, **kwargs)

    def generate_transaction_id(self):
        return f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.randbelow(1000):03d}"

    def __str__(self):
        return f"{self.transaction_id} - {self.get_transaction_type_display()}: KES {self.amount}"
    

# Interest Calculations
class InterestCalculation(models.Model):
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='interest_calculations')
    calculation_date = models.DateField()
    balance = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=4)
    interest_earned = models.DecimalField(max_digits=15, decimal_places=2)
    days_calculated = models.IntegerField()
    is_credited = models.BooleanField(default=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account.account_number} - {self.calculation_date}: KES {self.interest_earned}"

# Account Statements
class AccountStatement(models.Model):
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='statements')
    statement_date = models.DateField()
    from_date = models.DateField()
    to_date = models.DateField()
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2)
    total_credits = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_debits = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    statement_file = models.FileField(upload_to='statements/', blank=True)
    is_generated = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['account', 'from_date', 'to_date']

    def __str__(self):
        return f"{self.account.account_number} - {self.from_date} to {self.to_date}"

# Forex Rates (for multi-currency support)
class ForexRate(models.Model):
    base_currency = models.CharField(max_length=3, default='KES')  # Kenyan Shilling
    target_currency = models.CharField(max_length=3)  # USD, EUR, GBP, etc.
    buy_rate = models.DecimalField(max_digits=10, decimal_places=6)
    sell_rate = models.DecimalField(max_digits=10, decimal_places=6)
    mid_rate = models.DecimalField(max_digits=10, decimal_places=6)
    effective_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['base_currency', 'target_currency', 'effective_date']

    def __str__(self):
        return f"{self.base_currency}/{self.target_currency} - {self.mid_rate}"

# Notifications
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('transaction', 'Transaction Alert'),
        ('account', 'Account Alert'),
        ('loan', 'Loan Alert'),
        ('card', 'Card Alert'),
        ('security', 'Security Alert'),
        ('promotional', 'Promotional'),
        ('system', 'System Notification'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    )
    
    CHANNELS = (
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=15, choices=NOTIFICATION_TYPES)
    channel = models.CharField(max_length=10, choices=CHANNELS)
    title = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    related_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

# Security Events
class SecurityEvent(models.Model):
    EVENT_TYPES = (
        ('login_success', 'Successful Login'),
        ('login_failed', 'Failed Login'),
        ('password_change', 'Password Changed'),
        ('pin_change', 'PIN Changed'),
        ('card_blocked', 'Card Blocked'),
        ('account_locked', 'Account Locked'),
        ('suspicious_transaction', 'Suspicious Transaction'),
        ('fraud_detected', 'Fraud Detected'),
    )
    
    SEVERITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_events')
    event_type = models.CharField(max_length=25, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    device_info = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_security_events')
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_event_type_display()} - {self.severity}"

# Audit Trail
class AuditTrail(models.Model):
    ACTION_TYPES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('block', 'Block'),
        ('unblock', 'Unblock'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=15, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} {self.model_name} - {self.timestamp}"

# System Configuration
class SystemConfiguration(models.Model):
    CONFIG_TYPES = (
        ('general', 'General'),
        ('transaction', 'Transaction'),
        ('security', 'Security'),
        ('notification', 'Notification'),
        ('fee', 'Fee'),
        ('limit', 'Limit'),
    )
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    config_type = models.CharField(max_length=15, choices=CONFIG_TYPES, default='general')
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."

# Fee Structure
class FeeStructure(models.Model):
    TRANSACTION_TYPES = (
        ('atm_withdrawal_on_us', 'ATM Withdrawal (On-Us)'),
        ('atm_withdrawal_off_us', 'ATM Withdrawal (Off-Us)'),
        ('balance_inquiry_atm', 'Balance Inquiry (ATM)'),
        ('mobile_transfer_own', 'Mobile Transfer (Own Account)'),
        ('mobile_transfer_other', 'Mobile Transfer (Other Bank)'),
        ('agent_deposit', 'Agent Deposit'),
        ('agent_withdrawal', 'Agent Withdrawal'),
        ('card_issuance', 'Card Issuance'),
        ('card_replacement', 'Card Replacement'),
        ('statement_request', 'Statement Request'),
        ('checkbook_request', 'Checkbook Request'),
        ('loan_processing', 'Loan Processing'),
        ('account_maintenance', 'Account Maintenance'),
    )
    
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES, unique=True)
    fixed_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    percentage_fee = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.00'))
    minimum_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    maximum_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vat_applicable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    effective_from = models.DateTimeField()
    effective_to = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()}: KES {self.fixed_fee}"

# Customer Support Tickets
class SupportTicket(models.Model):
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    )
    
    CATEGORIES = (
        ('account', 'Account Issues'),
        ('card', 'Card Issues'),
        ('transaction', 'Transaction Issues'),
        ('loan', 'Loan Issues'),
        ('technical', 'Technical Issues'),
        ('general', 'General Inquiry'),
        ('complaint', 'Complaint'),
    )
    
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    category = models.CharField(max_length=15, choices=CATEGORIES)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    resolution = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = f"TKT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"

# Device Registration (for mobile banking security)
class DeviceRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registered_devices')
    device_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=50)  # Android, iOS, Web
    device_model = models.CharField(max_length=100, blank=True)
    os_version = models.CharField(max_length=50, blank=True)
    app_version = models.CharField(max_length=20, blank=True)
    is_trusted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    registration_ip = models.GenericIPAddressField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"

# Transaction Limits per user
class UserTransactionLimit(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='transaction_limits')
    daily_transfer_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('1000000.00'))
    daily_withdrawal_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('100000.00'))
    monthly_transfer_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('5000000.00'))
    single_transaction_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('500000.00'))
    
    # Current usage (resets daily/monthly)
    current_daily_transfers = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    current_daily_withdrawals = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    current_monthly_transfers = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    last_reset_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Limits for {self.user.username}"

# Standing Orders/Scheduled Payments
class StandingOrder(models.Model):
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )
    
    order_id = models.CharField(max_length=30, unique=True, editable=False)
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='standing_orders')
    beneficiary_account_number = models.CharField(max_length=20)
    beneficiary_name = models.CharField(max_length=200)
    beneficiary_bank = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES)
    reference = models.CharField(max_length=100)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_execution_date = models.DateField()
    last_execution_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    execution_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = f"SO{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.randbelow(100):02d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.beneficiary_name}: KES {self.amount}"
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"




# ATM Card Model
class ATMCard(models.Model):
    CARD_TYPES = (
        ('debit', 'Debit Card'),
        ('prepaid', 'Prepaid Card'),
    )
    
    CARD_STATUS = (
        ('active', 'Active'),
        ('blocked', 'Blocked'),
        ('expired', 'Expired'),
        ('damaged', 'Damaged'),
        ('cancelled', 'Cancelled'),
    )
    
    card_number = models.CharField(max_length=16, unique=True, editable=False)
    account = models.OneToOneField(BankAccount, on_delete=models.CASCADE, related_name='atm_card')
    cardholder_name = models.CharField(max_length=200)
    card_type = models.CharField(max_length=10, choices=CARD_TYPES, default='debit')
    cvv = models.CharField(max_length=3, editable=False)
    issue_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField()
    status = models.CharField(max_length=10, choices=CARD_STATUS, default='active')
    daily_withdrawal_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('40000.00'))
    daily_purchase_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('200000.00'))
    pin_tries_count = models.IntegerField(default=0)
    is_pin_blocked = models.BooleanField(default=False)
    issued_by_agent = models.ForeignKey(BankAgent, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.card_number:
            self.card_number = self.generate_card_number()
        if not self.cvv:
            self.cvv = self.generate_cvv()
        if not self.expiry_date:
            self.expiry_date = datetime.now().date() + timedelta(days=1095)  # 3 years
        super().save(*args, **kwargs)

    def generate_card_number(self):
        # Generate 16-digit card number
        return ''.join([str(secrets.randbelow(10)) for _ in range(16)])

    def generate_cvv(self):
        return ''.join([str(secrets.randbelow(10)) for _ in range(3)])

    def __str__(self):
        return f"**** **** **** {self.card_number[-4:]} - {self.account.customer.username}"



# Loan Types
class LoanType(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Personal Loan", "Business Loan"
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField()
    min_amount = models.DecimalField(max_digits=15, decimal_places=2)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2)
    min_tenure_months = models.IntegerField()
    max_tenure_months = models.IntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=4)  # Annual interest rate
    processing_fee_percentage = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('2.00'))
    requires_guarantor = models.BooleanField(default=False)
    requires_collateral = models.BooleanField(default=False)
    min_income_requirement = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    is_instant = models.BooleanField(default=False)  # For instant mobile loans
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# Loan Application
class LoanApplication(models.Model):
    APPLICATION_STATUS = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    application_id = models.CharField(max_length=30, unique=True, editable=False)
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_applications')
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    requested_amount = models.DecimalField(max_digits=15, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    tenure_months = models.IntegerField()
    purpose = models.TextField()
    monthly_income = models.DecimalField(max_digits=15, decimal_places=2)
    employment_details = models.TextField()
    status = models.CharField(max_length=15, choices=APPLICATION_STATUS, default='pending')
    
    # Credit scoring
    credit_score = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(300), MaxValueValidator(850)])
    risk_rating = models.CharField(max_length=10, blank=True)  # Low, Medium, High
    
    # Processing details
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_loans')
    rejection_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.application_id:
            self.application_id = f"LA{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.randbelow(100):02d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.application_id} - {self.applicant.username}: KES {self.requested_amount}"

# Active Loans
class Loan(models.Model):
    LOAN_STATUS = (
        ('active', 'Active'),
        ('paid_off', 'Paid Off'),
        ('defaulted', 'Defaulted'),
        ('written_off', 'Written Off'),
    )
    
    loan_number = models.CharField(max_length=30, unique=True, editable=False)
    application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE, related_name='loan')
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE)
    
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=4)
    tenure_months = models.IntegerField()
    monthly_installment = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Current loan status
    outstanding_principal = models.DecimalField(max_digits=15, decimal_places=2)
    outstanding_interest = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_paid = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Dates
    disbursement_date = models.DateTimeField()
    first_payment_date = models.DateField()
    maturity_date = models.DateField()
    last_payment_date = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=15, choices=LOAN_STATUS, default='active')
    days_in_arrears = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.loan_number:
            self.loan_number = f"LN{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.randbelow(100):02d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.loan_number} - {self.borrower.username}: KES {self.principal_amount}"

# Loan Payments
class LoanPayment(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed'),
    )
    
    payment_id = models.CharField(max_length=30, unique=True, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=15, decimal_places=2)
    penalty_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    payment_date = models.DateTimeField()
    due_date = models.DateField()
    status = models.CharField(max_length=15, choices=PAYMENT_STATUS, default='pending')
    payment_channel = models.CharField(max_length=20, blank=True)
    reference_number = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = f"LP{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.randbelow(100):02d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.payment_id} - {self.loan.loan_number}: KES {self.amount}"

# Mobile Banking Sessions
class MobileBankingSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    channel = models.CharField(max_length=20)  # 'ussd', 'mobile_app', 'sms'
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - {self.channel} - {self.session_id}"

# Bill Payment Services
class BillPaymentService(models.Model):
    name = models.CharField(max_length=100)  # e.g., "KPLC", "Safaricom", "Nairobi Water"
    code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=50)  # e.g., "Utilities", "Telecom", "Insurance"
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# Bill Payments
class BillPayment(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    payment_id = models.CharField(max_length=30, unique=True, editable=False)
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='bill_payments')
    service = models.ForeignKey(BillPaymentService, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=100)  # Customer's account with the service provider
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=15, choices=PAYMENT_STATUS, default='pending')
    reference_number = models.CharField(max_length=50, blank=True)
    receipt_number = models.CharField(max_length=50, blank=True)
    channel = models.CharField(max_length=20)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = f"BP{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.randbelow(100):02d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.payment_id} - {self.service.name}: KES {self.amount}"

# Card-less Withdrawal
class CardlessWithdrawal(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    withdrawal_code = models.CharField(max_length=10, unique=True, editable=False)
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='cardless_withdrawals')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    recipient_phone = models.CharField(max_length=15)
    recipient_name = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    atm_used = models.ForeignKey(ATMMachine, on_delete=models.SET_NULL, null=True, blank=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.withdrawal_code:
            self.withdrawal_code = ''.join(secrets.choice(string.digits) for _ in range(8))
        if not self.expires_at:
            self.expires_at = datetime.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.withdrawal_code} - KES {self.amount}"

# Agent Transaction Limits
class AgentTransactionLimit(models.Model):
    agent = models.OneToOneField(BankAgent, on_delete=models.CASCADE, related_name='transaction_limits')
    single_deposit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('300000.00'))
    single_withdrawal_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('70000.00'))
    daily_transaction_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('500000.00'))
    monthly_transaction_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('10000000.00'))
    
    # Current totals (reset daily/monthly)
    current_daily_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    current_monthly_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    last_reset_date = models.DateField(auto_now_add=True)
    
    created_at = models.DateTimeField(auto_now_add=True)