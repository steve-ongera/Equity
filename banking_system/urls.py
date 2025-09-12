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
    
  
]

