from django.shortcuts import render
# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    User, BankAccount, Transaction, Branch, BankAgent, ATMMachine,
    Loan, LoanApplication, SupportTicket, ForexRate, Notification,
    SecurityEvent, KYCDocument, BillPayment, InterestCalculation
)


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
import logging

# Set up logging
logger = logging.getLogger(__name__)

@csrf_protect
def login_view(request):
    """
    Login view that handles authentication for all user types
    and redirects to appropriate dashboard
    """
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Debug logging
        logger.info(f"Login attempt for username: {username}")
        
        # Validate input
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'auth/login.html')
        
        # Try to authenticate
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                # Handle AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'redirect_url': get_dashboard_url(user)
                    })
                
                return redirect_to_dashboard(user)
            else:
                messages.error(request, 'Your account has been deactivated. Please contact support.')
                logger.warning(f"Inactive user login attempt: {username}")
        else:
            messages.error(request, 'Invalid username or password.')
            logger.warning(f"Failed login attempt for username: {username}")
    
    return render(request, 'auth/login.html')

def redirect_to_dashboard(user):
    """
    Redirect user to appropriate dashboard based on user type
    """
    dashboard_url = get_dashboard_url(user)
    return redirect(dashboard_url)

def get_dashboard_url(user):
    """
    Get the appropriate dashboard URL for the user
    """
    # Check if user has user_type attribute
    if hasattr(user, 'user_type'):
        if user.user_type == 'admin':
            return 'admin_dashboard'
        elif user.user_type == 'staff':
            return 'staff_dashboard'
        elif user.user_type == 'agent':
            return 'agent_dashboard'
        else:  # customer
            return 'customer_dashboard'
    
    # Fallback: check if user is superuser/staff
    if user.is_superuser:
        return 'admin_dashboard'
    elif user.is_staff:
        return 'staff_dashboard'
    else:
        return 'customer_dashboard'

@login_required
def logout_view(request):
    """
    Logout view that logs out the user and redirects to login
    """
    username = request.user.username
    logout(request)
    messages.success(request, f'Goodbye {username}! You have been successfully logged out.')
    return redirect('login')

@login_required
def admin_dashboard(request):
    """
    Admin dashboard with comprehensive analytics and statistics
    """
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('login')
    
    # Calculate dashboard statistics
    context = get_admin_dashboard_context()
    return render(request, 'dashboards/admin_dashboard.html', context)

@login_required
def staff_dashboard(request):
    """
    Staff dashboard with operational metrics
    """
    if request.user.user_type not in ['staff', 'admin']:
        messages.error(request, 'Access denied. Staff privileges required.')
        return redirect('login')
    
    context = {
        'user': request.user,
        'pending_kyc': KYCDocument.objects.filter(status='pending').count(),
        'support_tickets': SupportTicket.objects.filter(status='open').count(),
        'recent_transactions': Transaction.objects.order_by('-created_at')[:10],
    }
    return render(request, 'dashboards/staff_dashboard.html', context)

@login_required
def agent_dashboard(request):
    """
    Bank Agent dashboard with agent-specific metrics
    """
    if request.user.user_type not in ['agent', 'admin']:
        messages.error(request, 'Access denied. Agent privileges required.')
        return redirect('login')
    
    try:
        agent_profile = request.user.agent_profile
        context = {
            'user': request.user,
            'agent': agent_profile,
            'daily_limit': agent_profile.daily_limit,
            'current_daily_total': agent_profile.current_daily_total,
            'remaining_daily': agent_profile.daily_limit - agent_profile.current_daily_total,
        }
    except BankAgent.DoesNotExist:
        messages.error(request, 'Agent profile not found.')
        return redirect('login')
    
    return render(request, 'dashboards/agent_dashboard.html', context)

@login_required
def customer_dashboard(request):
    """
    Customer dashboard with account information
    """
    if request.user.user_type not in ['customer', 'admin']:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    user_accounts = BankAccount.objects.filter(customer=request.user)
    recent_transactions = Transaction.objects.filter(
        account__customer=request.user
    ).order_by('-created_at')[:5]
    
    context = {
        'user': request.user,
        'accounts': user_accounts,
        'recent_transactions': recent_transactions,
        'total_balance': sum(account.balance for account in user_accounts),
    }
    return render(request, 'dashboards/customer_dashboard.html', context)

def get_admin_dashboard_context():
    """
    Get comprehensive dashboard context for admin
    """
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # Basic statistics
    total_customers = User.objects.filter(user_type='customer').count()
    total_accounts = BankAccount.objects.filter(status='active').count()
    total_transactions_today = Transaction.objects.filter(created_at__date=today).count()
    total_amount_today = Transaction.objects.filter(
        created_at__date=today,
        status='completed'
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    
    # Account type distribution
    account_types = BankAccount.objects.values(
        'account_type__name'
    ).annotate(count=Count('id')).order_by('-count')
    
    # Transaction trends (last 30 days)
    transaction_trends = Transaction.objects.filter(
        created_at__date__gte=thirty_days_ago
    ).extra(
        {'date': "date(created_at)"}
    ).values('date').annotate(
        count=Count('id'),
        amount=Sum('amount')
    ).order_by('date')
    
    # Branch performance
    branch_performance = Branch.objects.annotate(
        account_count=Count('bankaccount'),
        transaction_count=Count('bankaccount__transactions'),
        total_amount=Sum('bankaccount__transactions__amount')
    ).order_by('-account_count')
    
    # Loan statistics
    loan_stats = {
        'total_applications': LoanApplication.objects.count(),
        'pending_applications': LoanApplication.objects.filter(status='pending').count(),
        'active_loans': Loan.objects.filter(status='active').count(),
        'total_disbursed': Loan.objects.aggregate(Sum('principal_amount'))['principal_amount__sum'] or Decimal('0')
    }
    
    # ATM statistics
    atm_stats = {
        'total_atms': ATMMachine.objects.count(),
        'online_atms': ATMMachine.objects.filter(status='online').count(),
        'offline_atms': ATMMachine.objects.filter(status='offline').count(),
        'maintenance_atms': ATMMachine.objects.filter(status='maintenance').count(),
    }
    
    # Recent activities
    recent_activities = {
        'transactions': Transaction.objects.order_by('-created_at')[:5],
        'registrations': User.objects.filter(user_type='customer').order_by('-created_at')[:5],
        'support_tickets': SupportTicket.objects.order_by('-created_at')[:5],
    }
    
    return {
        'total_customers': total_customers,
        'total_accounts': total_accounts,
        'total_transactions_today': total_transactions_today,
        'total_amount_today': total_amount_today,
        'account_types': account_types,
        'transaction_trends': list(transaction_trends),
        'branch_performance': branch_performance[:5],
        'loan_stats': loan_stats,
        'atm_stats': atm_stats,
        'recent_activities': recent_activities,
    }

from django.db.models.functions import TruncDate
# AJAX endpoints for dashboard charts
@login_required
def get_transaction_data(request):
    """
    API endpoint for transaction chart data
    """
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    days = int(request.GET.get('days', 30))
    start_date = timezone.now().date() - timedelta(days=days)
    
    data = Transaction.objects.filter(
    created_at__date__gte=start_date,
    status='completed'
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id'),
        amount=Sum('amount')
    ).order_by('date')

    return JsonResponse({
        'labels': [item['date'].strftime('%Y-%m-%d') for item in data],  # now safe
        'counts': [item['count'] for item in data],
        'amounts': [float(item['amount']) for item in data]
    })

@login_required
def get_account_distribution_data(request):
    """
    API endpoint for account type distribution
    """
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    data = BankAccount.objects.values(
        'account_type__name'
    ).annotate(count=Count('id')).order_by('-count')
    
    return JsonResponse({
        'labels': [item['account_type__name'] for item in data],
        'data': [item['count'] for item in data]
    })

@login_required
def get_branch_performance_data(request):
    """
    API endpoint for branch performance data
    """
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    data = Branch.objects.annotate(
        account_count=Count('bankaccount'),
        transaction_count=Count('bankaccount__transactions', 
                              filter=Q(bankaccount__transactions__status='completed')),
        total_amount=Sum('bankaccount__transactions__amount',
                        filter=Q(bankaccount__transactions__status='completed'))
    ).order_by('-account_count')[:10]
    
    return JsonResponse({
        'labels': [branch.name for branch in data],
        'accounts': [branch.account_count for branch in data],
        'transactions': [branch.transaction_count or 0 for branch in data],
        'amounts': [float(branch.total_amount or 0) for branch in data]
    })

@login_required
def get_forex_data(request):
    """
    API endpoint for forex rates data
    """
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get latest forex rates
    latest_rates = ForexRate.objects.filter(
        effective_date__date=timezone.now().date()
    ).order_by('-effective_date')
    
    if not latest_rates.exists():
        # Get most recent rates if today's rates don't exist
        latest_rates = ForexRate.objects.order_by('-effective_date')[:10]
    
    return JsonResponse({
        'rates': [{
            'currency': rate.target_currency,
            'buy_rate': float(rate.buy_rate),
            'sell_rate': float(rate.sell_rate),
            'mid_rate': float(rate.mid_rate),
            'effective_date': rate.effective_date.strftime('%Y-%m-%d %H:%M')
        } for rate in latest_rates[:10]]
    })

@login_required
def get_monthly_summary_data(request):
    """
    API endpoint for monthly summary data
    """
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get data for the last 12 months
    twelve_months_ago = timezone.now().date().replace(day=1) - timedelta(days=365)
    
    monthly_data = Transaction.objects.filter(
        created_at__date__gte=twelve_months_ago,
        status='completed'
    ).extra(
        {'month': "DATE_FORMAT(created_at, '%%Y-%%m')"}
    ).values('month').annotate(
        transaction_count=Count('id'),
        total_amount=Sum('amount'),
        avg_amount=Avg('amount')
    ).order_by('month')
    
    return JsonResponse({
        'months': [item['month'] for item in monthly_data],
        'transaction_counts': [item['transaction_count'] for item in monthly_data],
        'total_amounts': [float(item['total_amount']) for item in monthly_data],
        'avg_amounts': [float(item['avg_amount']) for item in monthly_data]
    })

def custom_400(request, exception=None):
    return render(request, "errors/400.html", status=400)

def custom_403(request, exception=None):
    return render(request, "errors/403.html", status=403)

def custom_404(request, exception=None):
    return render(request, "errors/404.html", status=404)

def custom_500(request):
    return render(request, "errors/500.html", status=500)
