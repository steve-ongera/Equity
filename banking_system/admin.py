# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import *

# Custom User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'phone_number', 'kyc_status', 'is_active_customer', 'date_joined')
    list_filter = ('user_type', 'kyc_status', 'is_active_customer', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'national_id')
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Banking Information', {
            'fields': ('user_type', 'phone_number', 'national_id', 'date_of_birth', 
                      'address', 'city', 'postal_code', 'occupation', 'employer', 
                      'monthly_income', 'profile_photo', 'kyc_status', 'is_active_customer')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Banking Information', {
            'fields': ('user_type', 'phone_number', 'national_id', 'email', 'first_name', 'last_name')
        }),
    )

# Branch Admin
@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch_code', 'city', 'county', 'manager', 'is_active', 'phone_number')
    list_filter = ('county', 'is_active')
    search_fields = ('name', 'branch_code', 'city', 'county')
    readonly_fields = ('created_at',)

# Bank Agent Admin
@admin.register(BankAgent)
class BankAgentAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'agent_code', 'user', 'branch', 'business_phone', 'is_active')
    list_filter = ('branch', 'is_active')
    search_fields = ('business_name', 'agent_code', 'user__username', 'business_phone')
    readonly_fields = ('created_at', 'current_daily_total', 'current_monthly_total')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'agent_code', 'branch', 'business_name', 'business_address', 
                      'business_phone', 'license_number', 'is_active')
        }),
        ('Limits', {
            'fields': ('daily_limit', 'monthly_limit', 'current_daily_total', 'current_monthly_total')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        })
    )

# Account Type Admin
@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'minimum_balance', 'monthly_maintenance_fee', 'interest_rate', 'is_active')
    list_filter = ('is_active', 'requires_maintaining_balance', 'allows_overdraft')
    search_fields = ('name', 'code')

# Bank Account Admin
@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'customer', 'account_type', 'balance', 'available_balance', 'status', 'branch')
    list_filter = ('account_type', 'status', 'branch', 'is_primary')
    search_fields = ('account_number', 'customer__username', 'customer__first_name', 'customer__last_name')
    readonly_fields = ('account_number', 'created_at', 'updated_at', 'last_transaction_date')
    
    fieldsets = (
        ('Account Information', {
            'fields': ('account_number', 'customer', 'account_type', 'branch', 'created_by_agent', 'is_primary')
        }),
        ('Balance Information', {
            'fields': ('balance', 'available_balance', 'overdraft_limit')
        }),
        ('Status & Security', {
            'fields': ('status', 'pin_hash')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_transaction_date')
        })
    )

# ATM Card Admin
@admin.register(ATMCard)
class ATMCardAdmin(admin.ModelAdmin):
    list_display = ('masked_card_number', 'account', 'cardholder_name', 'card_type', 'status', 'expiry_date')
    list_filter = ('card_type', 'status', 'issue_date')
    search_fields = ('card_number', 'cardholder_name', 'account__account_number')
    readonly_fields = ('card_number', 'cvv', 'issue_date', 'created_at')
    
    def masked_card_number(self, obj):
        return f"**** **** **** {obj.card_number[-4:]}"
    masked_card_number.short_description = 'Card Number'
    
    fieldsets = (
        ('Card Information', {
            'fields': ('card_number', 'account', 'cardholder_name', 'card_type', 'cvv', 'expiry_date')
        }),
        ('Limits & Security', {
            'fields': ('daily_withdrawal_limit', 'daily_purchase_limit', 'status', 'pin_tries_count', 'is_pin_blocked')
        }),
        ('Issuance', {
            'fields': ('issued_by_agent', 'issue_date', 'created_at')
        })
    )

# ATM Machine Admin
@admin.register(ATMMachine)
class ATMMachineAdmin(admin.ModelAdmin):
    list_display = ('atm_id', 'location_name', 'city', 'county', 'status', 'cash_available', 'branch')
    list_filter = ('status', 'city', 'county', 'branch', 'supports_deposit', 'supports_cardless')
    search_fields = ('atm_id', 'location_name', 'address')
    readonly_fields = ('created_at', 'last_maintenance')
    
    fieldsets = (
        ('Location Information', {
            'fields': ('atm_id', 'location_name', 'address', 'city', 'county', 'latitude', 'longitude', 'branch')
        }),
        ('Cash Management', {
            'fields': ('cash_available', 'max_cash_capacity', 'status')
        }),
        ('Limits & Features', {
            'fields': ('daily_withdrawal_limit', 'single_withdrawal_limit', 'supports_deposit', 'supports_cardless')
        }),
        ('Maintenance', {
            'fields': ('last_maintenance', 'created_at')
        })
    )

# Transaction Admin
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'account', 'transaction_type', 'amount', 'fee', 'channel', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'channel', 'created_at')
    search_fields = ('transaction_id', 'account__account_number', 'reference_number', 'description')
    readonly_fields = ('transaction_id', 'created_at', 'processed_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_id', 'account', 'transaction_type', 'amount', 'fee', 'total_amount', 'status')
        }),
        ('Transfer Information', {
            'fields': ('beneficiary_account', 'beneficiary_name', 'beneficiary_bank'),
            'classes': ('collapse',)
        }),
        ('Processing Details', {
            'fields': ('channel', 'reference_number', 'description', 'atm_machine', 'agent', 'branch')
        }),
        ('Balance Information', {
            'fields': ('balance_before', 'balance_after')
        }),
        ('System Information', {
            'fields': ('device_info', 'ip_address', 'session_id', 'created_at', 'processed_at')
        })
    )

# Loan Type Admin
@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'min_amount', 'max_amount', 'interest_rate', 'is_instant', 'is_active')
    list_filter = ('is_instant', 'is_active', 'requires_guarantor', 'requires_collateral')
    search_fields = ('name', 'code')

# Loan Application Admin
@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_id', 'applicant', 'loan_type', 'requested_amount', 'status', 'created_at')
    list_filter = ('status', 'loan_type', 'created_at')
    search_fields = ('application_id', 'applicant__username', 'applicant__first_name')
    readonly_fields = ('application_id', 'created_at', 'processed_at')
    
    fieldsets = (
        ('Application Details', {
            'fields': ('application_id', 'applicant', 'account', 'loan_type', 'requested_amount', 
                      'approved_amount', 'tenure_months', 'purpose')
        }),
        ('Applicant Information', {
            'fields': ('monthly_income', 'employment_details')
        }),
        ('Assessment', {
            'fields': ('credit_score', 'risk_rating', 'status', 'rejection_reason')
        }),
        ('Processing', {
            'fields': ('processed_by', 'created_at', 'processed_at')
        })
    )

# Active Loan Admin
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('loan_number', 'borrower', 'loan_type', 'principal_amount', 'outstanding_principal', 'status', 'days_in_arrears')
    list_filter = ('status', 'loan_type', 'disbursement_date')
    search_fields = ('loan_number', 'borrower__username', 'borrower__first_name')
    readonly_fields = ('loan_number', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Loan Details', {
            'fields': ('loan_number', 'application', 'borrower', 'account', 'loan_type')
        }),
        ('Amount & Terms', {
            'fields': ('principal_amount', 'interest_rate', 'tenure_months', 'monthly_installment')
        }),
        ('Current Status', {
            'fields': ('outstanding_principal', 'outstanding_interest', 'total_paid', 'status', 'days_in_arrears')
        }),
        ('Dates', {
            'fields': ('disbursement_date', 'first_payment_date', 'maturity_date', 'last_payment_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )

# Loan Payment Admin
@admin.register(LoanPayment)
class LoanPaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'loan', 'amount', 'principal_amount', 'interest_amount', 'payment_date', 'status')
    list_filter = ('status', 'payment_date')
    search_fields = ('payment_id', 'loan__loan_number', 'reference_number')
    readonly_fields = ('payment_id', 'created_at')

# Mobile Banking Session Admin
@admin.register(MobileBankingSession)
class MobileBankingSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'user', 'phone_number', 'channel', 'is_active', 'last_activity', 'expires_at')
    list_filter = ('channel', 'is_active', 'created_at')
    search_fields = ('session_id', 'user__username', 'phone_number')

# Bill Payment Service Admin
@admin.register(BillPaymentService)
class BillPaymentServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'fee', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'code')

# Bill Payment Admin
@admin.register(BillPayment)
class BillPaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'account', 'service', 'amount', 'fee', 'status', 'created_at')
    list_filter = ('service', 'status', 'channel')
    search_fields = ('payment_id', 'account__account_number', 'account_number', 'receipt_number')
    readonly_fields = ('payment_id', 'created_at', 'processed_at')

# Cardless Withdrawal Admin
@admin.register(CardlessWithdrawal)
class CardlessWithdrawalAdmin(admin.ModelAdmin):
    list_display = ('withdrawal_code', 'account', 'amount', 'recipient_phone', 'status', 'expires_at')
    list_filter = ('status', 'created_at')
    search_fields = ('withdrawal_code', 'account__account_number', 'recipient_phone')
    readonly_fields = ('withdrawal_code', 'created_at', 'used_at')

# Agent Transaction Limit Admin
@admin.register(AgentTransactionLimit)
class AgentTransactionLimitAdmin(admin.ModelAdmin):
    list_display = ('agent', 'single_deposit_limit', 'single_withdrawal_limit', 'daily_transaction_limit', 'current_daily_total')
    search_fields = ('agent__business_name', 'agent__agent_code')
    readonly_fields = ('current_daily_total', 'current_monthly_total', 'created_at')

# KYC Document Admin
@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'document_number', 'status', 'verified_by', 'created_at')
    list_filter = ('document_type', 'status', 'created_at')
    search_fields = ('user__username', 'document_number')
    readonly_fields = ('created_at', 'verified_at')
    
    actions = ['approve_documents', 'reject_documents']
    
    def approve_documents(self, request, queryset):
        queryset.update(status='verified', verified_by=request.user)
    approve_documents.short_description = "Approve selected KYC documents"
    
    def reject_documents(self, request, queryset):
        queryset.update(status='rejected', verified_by=request.user)
    reject_documents.short_description = "Reject selected KYC documents"

# Interest Calculation Admin
@admin.register(InterestCalculation)
class InterestCalculationAdmin(admin.ModelAdmin):
    list_display = ('account', 'calculation_date', 'balance', 'interest_rate', 'interest_earned', 'is_credited')
    list_filter = ('calculation_date', 'is_credited')
    search_fields = ('account__account_number',)
    readonly_fields = ('created_at',)

# Account Statement Admin
@admin.register(AccountStatement)
class AccountStatementAdmin(admin.ModelAdmin):
    list_display = ('account', 'statement_date', 'from_date', 'to_date', 'opening_balance', 'closing_balance', 'is_generated')
    list_filter = ('statement_date', 'is_generated')
    search_fields = ('account__account_number',)
    readonly_fields = ('created_at',)

# Forex Rate Admin
@admin.register(ForexRate)
class ForexRateAdmin(admin.ModelAdmin):
    list_display = ('base_currency', 'target_currency', 'buy_rate', 'sell_rate', 'mid_rate', 'effective_date')
    list_filter = ('base_currency', 'target_currency', 'effective_date')
    search_fields = ('base_currency', 'target_currency')

# Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'channel', 'title', 'status', 'is_read', 'created_at')
    list_filter = ('notification_type', 'channel', 'status', 'is_read')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at', 'sent_at', 'read_at')

# Security Event Admin
@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'severity', 'ip_address', 'location', 'is_resolved', 'created_at')
    list_filter = ('event_type', 'severity', 'is_resolved', 'created_at')
    search_fields = ('user__username', 'ip_address', 'location')
    readonly_fields = ('created_at', 'resolved_at')
    
    actions = ['mark_resolved']
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_resolved=True, resolved_by=request.user, resolved_at=timezone.now())
    mark_resolved.short_description = "Mark selected events as resolved"

# Audit Trail Admin
@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_repr', 'ip_address', 'timestamp')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'model_name', 'object_repr')
    readonly_fields = ('timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

# System Configuration Admin
@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'config_type', 'value_preview', 'is_active', 'created_by', 'updated_at')
    list_filter = ('config_type', 'is_active')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def value_preview(self, obj):
        return obj.value[:50] + "..." if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Value'

# Fee Structure Admin
@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'fixed_fee', 'percentage_fee', 'minimum_fee', 'maximum_fee', 'vat_applicable', 'is_active')
    list_filter = ('vat_applicable', 'is_active', 'effective_from')
    search_fields = ('transaction_type',)
    readonly_fields = ('created_at', 'updated_at')

# Support Ticket Admin
@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'customer', 'category', 'subject', 'priority', 'status', 'assigned_to', 'created_at')
    list_filter = ('category', 'priority', 'status', 'created_at')
    search_fields = ('ticket_number', 'customer__username', 'subject')
    readonly_fields = ('ticket_number', 'created_at', 'resolved_at')
    
    actions = ['assign_to_me', 'mark_resolved']
    
    def assign_to_me(self, request, queryset):
        queryset.update(assigned_to=request.user, status='in_progress')
    assign_to_me.short_description = "Assign selected tickets to me"
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='resolved', resolved_at=timezone.now())
    mark_resolved.short_description = "Mark selected tickets as resolved"

# Device Registration Admin
@admin.register(DeviceRegistration)
class DeviceRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_name', 'device_type', 'device_model', 'is_trusted', 'is_active', 'last_used')
    list_filter = ('device_type', 'is_trusted', 'is_active', 'created_at')
    search_fields = ('user__username', 'device_name', 'device_id')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['mark_trusted', 'deactivate_devices']
    
    def mark_trusted(self, request, queryset):
        queryset.update(is_trusted=True)
    mark_trusted.short_description = "Mark selected devices as trusted"
    
    def deactivate_devices(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_devices.short_description = "Deactivate selected devices"

# User Transaction Limit Admin
@admin.register(UserTransactionLimit)
class UserTransactionLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_transfer_limit', 'daily_withdrawal_limit', 'single_transaction_limit', 'last_reset_date')
    search_fields = ('user__username',)
    readonly_fields = ('current_daily_transfers', 'current_daily_withdrawals', 'current_monthly_transfers', 'created_at', 'updated_at')

# Standing Order Admin
@admin.register(StandingOrder)
class StandingOrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'account', 'beneficiary_name', 'amount', 'frequency', 'status', 'next_execution_date')
    list_filter = ('frequency', 'status', 'start_date')
    search_fields = ('order_id', 'account__account_number', 'beneficiary_name', 'beneficiary_account_number')
    readonly_fields = ('order_id', 'created_at', 'updated_at', 'last_execution_date')
    
    fieldsets = (
        ('Order Details', {
            'fields': ('order_id', 'account', 'amount', 'frequency', 'reference', 'status')
        }),
        ('Beneficiary Information', {
            'fields': ('beneficiary_account_number', 'beneficiary_name', 'beneficiary_bank')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'next_execution_date', 'last_execution_date')
        }),
        ('Statistics', {
            'fields': ('execution_count', 'failed_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )

# Custom Admin Site Configuration
admin.site.site_header = "Equity Bank Management System"
admin.site.site_title = "Equity Bank Admin"
admin.site.index_title = "Welcome to Equity Bank Administration"

# Add custom CSS
class CustomAdminMixin:
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }

# Apply custom styling to all admin classes
for model_admin in [UserAdmin, BranchAdmin, BankAgentAdmin, BankAccountAdmin, 
                   ATMCardAdmin, ATMMachineAdmin, TransactionAdmin]:
    if hasattr(model_admin, 'Media'):
        model_admin.Media.css = {'all': ('admin/css/custom_admin.css',)}
    else:
        model_admin.Media = type('Media', (), {'css': {'all': ('admin/css/custom_admin.css',)}})

# Dashboard customizations
def get_dashboard_stats():
    """Get dashboard statistics for admin overview"""
    from django.db.models import Sum, Count, Q
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    stats = {
        'total_customers': User.objects.filter(user_type='customer').count(),
        'active_accounts': BankAccount.objects.filter(status='active').count(),
        'total_balance': BankAccount.objects.aggregate(
            total=Sum('balance'))['total'] or 0,
        'transactions_today': Transaction.objects.filter(
            created_at__date=today).count(),
        'transactions_week': Transaction.objects.filter(
            created_at__date__gte=week_ago).count(),
        'active_loans': Loan.objects.filter(status='active').count(),
        'pending_kyc': KYCDocument.objects.filter(status='pending').count(),
        'active_agents': BankAgent.objects.filter(is_active=True).count(),
    }
    return stats

# Custom admin views can be added here for reports and dashboards