# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('agent-dashboard/', views.agent_dashboard, name='agent_dashboard'),
    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),
    
    # API endpoints for AJAX data
    path('api/transaction-data/', views.get_transaction_data, name='api_transaction_data'),
    path('api/account-distribution/', views.get_account_distribution_data, name='api_account_distribution'),
    path('api/branch-performance/', views.get_branch_performance_data, name='api_branch_performance'),
    path('api/forex-data/', views.get_forex_data, name='api_forex_data'),
    path('api/monthly-summary/', views.get_monthly_summary_data, name='api_monthly_summary'),

    # Transaction Views
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdrawal/', views.withdrawal_view, name='withdrawal'),
    path('transfer/', views.transfer_view, name='transfer'),
    
    # API Endpoints
    path('api/deposit/', views.api_deposit, name='api_deposit'),
    path('api/withdrawal/', views.api_withdrawal, name='api_withdrawal'),
    path('api/transfer/', views.api_transfer, name='api_transfer'),
    path('api/verify-account/', views.api_verify_account, name='api_verify_account'),


    # Customer Profile URLs
    path('profile/', views.customer_profile, name='customer_profile'),
    path('transaction-history/', views.transaction_history, name='transaction_history'),
    path('change-password/', views.change_password, name='change_password'),
    path('profile-settings/', views.profile_settings, name='profile_settings'),
    path('financial-summary/', views.financial_summary, name='financial_summary'),
    path('notifications/', views.notifications, name='notifications'),
    path('account-statements/', views.account_statements, name='account_statements'),
    path('download-statement/<int:statement_id>/', views.download_statement, name='download_statement'),

    #admin urls 
    path('analytics/', views.analytics, name='analytics'),
    
    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('kyc/', views.kyc_management, name='kyc_management'),
    path('security/events/', views.security_events, name='security_events'),
    path('accounts/', views.account_list, name='account_list'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('loans/applications/', views.loan_applications, name='loan_applications'),
    path('loans/active/', views.active_loans, name='active_loans'),
    path('branches/', views.branch_list, name='branch_list'),
    path('atms/', views.atm_list, name='atm_list'),
    path('reports/financial/', views.financial_reports, name='financial_reports'),
    path('reports/operational/', views.operational_reports, name='operational_reports'),
    path('support/tickets/', views.support_tickets, name='support_tickets'),
    path('system/settings/', views.system_settings, name='system_settings'),
    path('system/fees/', views.fee_structure, name='fee_structure'),
    path('system/audit/', views.audit_trail, name='audit_trail'),
    
  
]

