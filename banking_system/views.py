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


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import json
from datetime import datetime, timedelta
from .models import (
    User, BankAccount, Transaction, Notification, 
    FeeStructure, UserTransactionLimit, BankAgent
)

@login_required
def customer_dashboard(request):
    """Main customer dashboard view"""
    try:
        # Get user's primary account or first active account
        account = BankAccount.objects.filter(
            customer=request.user,
            status='active'
        ).first()
        
        if not account:
            messages.error(request, "No active account found. Please contact customer service.")
            return render(request, 'dashboards/customer_dashboard.html', {'no_account': True})
        
        # Get recent transactions (last 10)
        recent_transactions = Transaction.objects.filter(
            account=account
        ).order_by('-created_at')[:10]
        
        # Get transaction summary for current month
        current_month = timezone.now().replace(day=1)
        monthly_transactions = Transaction.objects.filter(
            account=account,
            created_at__gte=current_month,
            status='completed'
        )
        
        # Calculate monthly stats
        monthly_deposits = monthly_transactions.filter(
            transaction_type='deposit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        monthly_withdrawals = monthly_transactions.filter(
            transaction_type='withdrawal'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        monthly_transfers_sent = monthly_transactions.filter(
            transaction_type='transfer'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Get user transaction limits
        try:
            limits = UserTransactionLimit.objects.get(user=request.user)
        except UserTransactionLimit.DoesNotExist:
            # Create default limits if they don't exist
            limits = UserTransactionLimit.objects.create(user=request.user)
        
        # Get unread notifications
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:5]
        
        context = {
            'account': account,
            'recent_transactions': recent_transactions,
            'monthly_deposits': monthly_deposits,
            'monthly_withdrawals': monthly_withdrawals,
            'monthly_transfers': monthly_transfers_sent,
            'limits': limits,
            'unread_notifications': unread_notifications,
        }
        
        return render(request, 'dashboards/customer_dashboard.html', context)
    
    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return render(request, 'dashboards/customer_dashboard.html', {'error': True})

@login_required
def deposit_view(request):
    """Deposit money view"""
    account = BankAccount.objects.filter(
        customer=request.user,
        status='active'
    ).first()
    
    if not account:
        messages.error(request, "No active account found.")
        return redirect('customer_dashboard')
    
    # Get available agents for deposit
    agents = BankAgent.objects.filter(is_active=True)
    
    context = {
        'account': account,
        'agents': agents,
    }
    
    return render(request, 'customer/deposit.html', context)

@login_required
def withdrawal_view(request):
    """Withdraw money view"""
    account = BankAccount.objects.filter(
        customer=request.user,
        status='active'
    ).first()
    
    if not account:
        messages.error(request, "No active account found.")
        return redirect('customer_dashboard')
    
    # Get user limits
    try:
        limits = UserTransactionLimit.objects.get(user=request.user)
    except UserTransactionLimit.DoesNotExist:
        limits = UserTransactionLimit.objects.create(user=request.user)
    
    # Get available agents
    agents = BankAgent.objects.filter(is_active=True)
    
    context = {
        'account': account,
        'limits': limits,
        'agents': agents,
    }
    
    return render(request, 'customer/withdrawal.html', context)

@login_required
def transfer_view(request):
    """Transfer money view"""
    account = BankAccount.objects.filter(
        customer=request.user,
        status='active'
    ).first()
    
    if not account:
        messages.error(request, "No active account found.")
        return redirect('customer_dashboard')
    
    # Get user limits
    try:
        limits = UserTransactionLimit.objects.get(user=request.user)
    except UserTransactionLimit.DoesNotExist:
        limits = UserTransactionLimit.objects.create(user=request.user)
    
    context = {
        'account': account,
        'limits': limits,
    }
    
    return render(request, 'customer/transfer.html', context)

# AJAX API Views
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_deposit(request):
    """API endpoint for deposit"""
    try:
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))
        agent_id = data.get('agent_id')
        
        if amount <= 0:
            return JsonResponse({'success': False, 'error': 'Invalid amount'})
        
        # Get user's account
        account = BankAccount.objects.filter(
            customer=request.user,
            status='active'
        ).first()
        
        if not account:
            return JsonResponse({'success': False, 'error': 'No active account found'})
        
        # Get agent if specified
        agent = None
        if agent_id:
            agent = get_object_or_404(BankAgent, id=agent_id, is_active=True)
        
        # Calculate fee
        fee = calculate_transaction_fee('agent_deposit', amount)
        total_deposit = amount - fee
        
        # Create transaction
        balance_before = account.balance
        account.balance += total_deposit
        account.available_balance += total_deposit
        account.last_transaction_date = timezone.now()
        account.save()
        
        # Create transaction record
        transaction = Transaction.objects.create(
            account=account,
            transaction_type='deposit',
            amount=amount,
            fee=fee,
            total_amount=total_deposit,
            balance_before=balance_before,
            balance_after=account.balance,
            channel='agent',
            description=f'Cash deposit via agent {agent.business_name if agent else "N/A"}',
            status='completed',
            agent=agent,
            processed_at=timezone.now()
        )
        
        # Send notification
        send_transaction_notification(
            user=request.user,
            transaction=transaction,
            notification_type='deposit'
        )
        
        return JsonResponse({
            'success': True,
            'transaction_id': transaction.transaction_id,
            'new_balance': float(account.balance),
            'fee': float(fee)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_withdrawal(request):
    """API endpoint for withdrawal"""
    try:
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))
        agent_id = data.get('agent_id')
        
        if amount <= 0:
            return JsonResponse({'success': False, 'error': 'Invalid amount'})
        
        # Get user's account
        account = BankAccount.objects.filter(
            customer=request.user,
            status='active'
        ).first()
        
        if not account:
            return JsonResponse({'success': False, 'error': 'No active account found'})
        
        # Check limits
        limits = UserTransactionLimit.objects.get_or_create(user=request.user)[0]
        
        if amount > limits.single_transaction_limit:
            return JsonResponse({
                'success': False, 
                'error': f'Amount exceeds single transaction limit of KES {limits.single_transaction_limit:,.2f}'
            })
        
        # Check daily limit
        today = timezone.now().date()
        daily_withdrawals = Transaction.objects.filter(
            account=account,
            transaction_type='withdrawal',
            created_at__date=today,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        if daily_withdrawals + amount > limits.daily_withdrawal_limit:
            return JsonResponse({
                'success': False,
                'error': f'Daily withdrawal limit of KES {limits.daily_withdrawal_limit:,.2f} exceeded'
            })
        
        # Get agent if specified
        agent = None
        if agent_id:
            agent = get_object_or_404(BankAgent, id=agent_id, is_active=True)
        
        # Calculate fee
        fee = calculate_transaction_fee('agent_withdrawal', amount)
        total_debit = amount + fee
        
        # Check balance
        if account.available_balance < total_debit:
            return JsonResponse({'success': False, 'error': 'Insufficient funds'})
        
        # Process withdrawal
        balance_before = account.balance
        account.balance -= total_debit
        account.available_balance -= total_debit
        account.last_transaction_date = timezone.now()
        account.save()
        
        # Create transaction record
        transaction = Transaction.objects.create(
            account=account,
            transaction_type='withdrawal',
            amount=amount,
            fee=fee,
            total_amount=total_debit,
            balance_before=balance_before,
            balance_after=account.balance,
            channel='agent',
            description=f'Cash withdrawal via agent {agent.business_name if agent else "N/A"}',
            status='completed',
            agent=agent,
            processed_at=timezone.now()
        )
        
        # Send notification
        send_transaction_notification(
            user=request.user,
            transaction=transaction,
            notification_type='withdrawal'
        )
        
        return JsonResponse({
            'success': True,
            'transaction_id': transaction.transaction_id,
            'new_balance': float(account.balance),
            'fee': float(fee)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_transfer(request):
    """API endpoint for transfer"""
    try:
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))
        beneficiary_account_number = data.get('account_number', '').strip()
        beneficiary_name = data.get('beneficiary_name', '').strip()
        reference = data.get('reference', '').strip()
        
        if amount <= 0:
            return JsonResponse({'success': False, 'error': 'Invalid amount'})
        
        if not beneficiary_account_number:
            return JsonResponse({'success': False, 'error': 'Beneficiary account number required'})
        
        # Get sender's account
        sender_account = BankAccount.objects.filter(
            customer=request.user,
            status='active'
        ).first()
        
        if not sender_account:
            return JsonResponse({'success': False, 'error': 'No active account found'})
        
        # Check limits
        limits = UserTransactionLimit.objects.get_or_create(user=request.user)[0]
        
        if amount > limits.single_transaction_limit:
            return JsonResponse({
                'success': False,
                'error': f'Amount exceeds single transaction limit of KES {limits.single_transaction_limit:,.2f}'
            })
        
        # Check daily limit
        today = timezone.now().date()
        daily_transfers = Transaction.objects.filter(
            account=sender_account,
            transaction_type='transfer',
            created_at__date=today,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        if daily_transfers + amount > limits.daily_transfer_limit:
            return JsonResponse({
                'success': False,
                'error': f'Daily transfer limit of KES {limits.daily_transfer_limit:,.2f} exceeded'
            })
        
        # Find beneficiary account
        try:
            beneficiary_account = BankAccount.objects.get(
                account_number=beneficiary_account_number,
                status='active'
            )
        except BankAccount.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Beneficiary account not found'})
        
        # Check if trying to transfer to same account
        if sender_account.id == beneficiary_account.id:
            return JsonResponse({'success': False, 'error': 'Cannot transfer to same account'})
        
        # Calculate fee
        fee = calculate_transaction_fee('mobile_transfer_own', amount)
        total_debit = amount + fee
        
        # Check balance
        if sender_account.available_balance < total_debit:
            return JsonResponse({'success': False, 'error': 'Insufficient funds'})
        
        # Process transfer (debit sender)
        sender_balance_before = sender_account.balance
        sender_account.balance -= total_debit
        sender_account.available_balance -= total_debit
        sender_account.last_transaction_date = timezone.now()
        sender_account.save()
        
        # Credit beneficiary
        beneficiary_balance_before = beneficiary_account.balance
        beneficiary_account.balance += amount
        beneficiary_account.available_balance += amount
        beneficiary_account.last_transaction_date = timezone.now()
        beneficiary_account.save()
        
        # Create debit transaction for sender
        debit_transaction = Transaction.objects.create(
            account=sender_account,
            transaction_type='transfer',
            amount=amount,
            fee=fee,
            total_amount=total_debit,
            balance_before=sender_balance_before,
            balance_after=sender_account.balance,
            channel='mobile',
            description=f'Transfer to {beneficiary_name or beneficiary_account.customer.get_full_name()}',
            reference_number=reference,
            status='completed',
            beneficiary_account=beneficiary_account,
            beneficiary_name=beneficiary_name or beneficiary_account.customer.get_full_name(),
            processed_at=timezone.now()
        )
        
        # Create credit transaction for beneficiary
        credit_transaction = Transaction.objects.create(
            account=beneficiary_account,
            transaction_type='deposit',
            amount=amount,
            fee=Decimal('0'),
            total_amount=amount,
            balance_before=beneficiary_balance_before,
            balance_after=beneficiary_account.balance,
            channel='mobile',
            description=f'Transfer from {sender_account.customer.get_full_name()}',
            reference_number=reference,
            status='completed',
            processed_at=timezone.now()
        )
        
        # Send notifications
        send_transaction_notification(
            user=request.user,
            transaction=debit_transaction,
            notification_type='transfer_sent'
        )
        
        send_transaction_notification(
            user=beneficiary_account.customer,
            transaction=credit_transaction,
            notification_type='transfer_received'
        )
        
        return JsonResponse({
            'success': True,
            'transaction_id': debit_transaction.transaction_id,
            'new_balance': float(sender_account.balance),
            'fee': float(fee),
            'beneficiary_name': beneficiary_account.customer.get_full_name()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["POST"])
@login_required
def api_verify_account(request):
    """API endpoint to verify account number"""
    try:
        data = json.loads(request.body)
        account_number = data.get('account_number', '').strip()
        
        if not account_number:
            return JsonResponse({'success': False, 'error': 'Account number required'})
        
        try:
            account = BankAccount.objects.get(
                account_number=account_number,
                status='active'
            )
            
            return JsonResponse({
                'success': True,
                'account_name': account.customer.get_full_name(),
                'account_type': account.account_type.name
            })
            
        except BankAccount.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Account not found'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Helper functions
def calculate_transaction_fee(transaction_type, amount):
    """Calculate transaction fee based on type and amount"""
    try:
        fee_structure = FeeStructure.objects.get(
            transaction_type=transaction_type,
            is_active=True
        )
        
        # Calculate percentage fee
        percentage_fee = amount * (fee_structure.percentage_fee / 100)
        
        # Use fixed fee or percentage fee, whichever is higher
        calculated_fee = max(fee_structure.fixed_fee, percentage_fee)
        
        # Apply minimum and maximum limits
        if calculated_fee < fee_structure.minimum_fee:
            calculated_fee = fee_structure.minimum_fee
        
        if fee_structure.maximum_fee and calculated_fee > fee_structure.maximum_fee:
            calculated_fee = fee_structure.maximum_fee
        
        return calculated_fee
        
    except FeeStructure.DoesNotExist:
        # Default fees if fee structure not found
        default_fees = {
            'agent_deposit': Decimal('10.00'),
            'agent_withdrawal': Decimal('35.00'),
            'mobile_transfer_own': Decimal('25.00'),
            'mobile_transfer_other': Decimal('50.00'),
        }
        return default_fees.get(transaction_type, Decimal('0.00'))

def send_transaction_notification(user, transaction, notification_type):
    """Send transaction notification via email and in-app"""
    try:
        # Create notification messages
        notification_messages = {
            'deposit': {
                'title': 'Money Received',
                'message': f'You have received KES {transaction.amount:,.2f} in your account {transaction.account.account_number}. Your new balance is KES {transaction.balance_after:,.2f}.',
                'email_subject': 'Equity Bank - Money Received'
            },
            'withdrawal': {
                'title': 'Money Withdrawn',
                'message': f'You have withdrawn KES {transaction.amount:,.2f} from your account {transaction.account.account_number}. Fee: KES {transaction.fee:,.2f}. Your new balance is KES {transaction.balance_after:,.2f}.',
                'email_subject': 'Equity Bank - Withdrawal Confirmation'
            },
            'transfer_sent': {
                'title': 'Money Sent',
                'message': f'You have sent KES {transaction.amount:,.2f} to {transaction.beneficiary_name}. Fee: KES {transaction.fee:,.2f}. Your new balance is KES {transaction.balance_after:,.2f}.',
                'email_subject': 'Equity Bank - Transfer Sent'
            },
            'transfer_received': {
                'title': 'Money Received',
                'message': f'You have received KES {transaction.amount:,.2f} from {transaction.description.replace("Transfer from ", "")}. Your new balance is KES {transaction.balance_after:,.2f}.',
                'email_subject': 'Equity Bank - Money Received'
            }
        }
        
        notification_data = notification_messages.get(notification_type, {
            'title': 'Transaction Alert',
            'message': f'Transaction of KES {transaction.amount:,.2f} processed.',
            'email_subject': 'Equity Bank - Transaction Alert'
        })
        
        # Create in-app notification
        Notification.objects.create(
            user=user,
            notification_type='transaction',
            channel='in_app',
            title=notification_data['title'],
            message=notification_data['message'],
            status='sent',
            related_transaction=transaction,
            sent_at=timezone.now()
        )
        
        # Send email notification
        if user.email:
            email_message = f"""
Dear {user.get_full_name() or user.username},

{notification_data['message']}

Transaction Details:
- Transaction ID: {transaction.transaction_id}
- Date: {transaction.created_at.strftime('%d/%m/%Y %H:%M:%S')}
- Channel: {transaction.get_channel_display()}

For any inquiries, please contact our customer service.

Best regards,
Equity Bank Kenya
            """
            
            send_mail(
                subject=notification_data['email_subject'],
                message=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True
            )
            
            # Create email notification record
            Notification.objects.create(
                user=user,
                notification_type='transaction',
                channel='email',
                title=notification_data['email_subject'],
                message=email_message,
                status='sent',
                related_transaction=transaction,
                sent_at=timezone.now()
            )
            
    except Exception as e:
        print(f"Error sending notification: {e}")


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
from django.contrib.auth.forms import PasswordChangeForm
from django.forms import ModelForm
from django import forms
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    User, BankAccount, Transaction, Notification, AccountStatement,
    UserTransactionLimit, ATMCard, Loan, BillPayment, InterestCalculation
)

# Customer Profile Form
class CustomerProfileForm(ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 
            'address', 'city', 'postal_code', 'occupation', 
            'employer', 'monthly_income'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'employer': forms.TextInput(attrs={'class': 'form-control'}),
            'monthly_income': forms.NumberInput(attrs={'class': 'form-control'}),
        }

@login_required
def customer_profile(request):
    """Customer profile view with edit functionality"""
    user = request.user
    
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('customer_profile')
    else:
        form = CustomerProfileForm(instance=user)
    
    # Get user's accounts and basic stats
    accounts = BankAccount.objects.filter(customer=user)
    total_balance = accounts.aggregate(Sum('balance'))['balance__sum'] or Decimal('0.00')
    
    context = {
        'form': form,
        'user': user,
        'accounts': accounts,
        'total_balance': total_balance,
    }
    return render(request, 'customer/profile.html', context)

@login_required
def transaction_history(request):
    """Transaction history with filtering and pagination"""
    user_accounts = BankAccount.objects.filter(customer=request.user)
    
    # Get filter parameters
    account_filter = request.GET.get('account', '')
    transaction_type = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Build query
    transactions = Transaction.objects.filter(account__in=user_accounts)
    
    if account_filter:
        transactions = transactions.filter(account__account_number=account_filter)
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if date_from:
        transactions = transactions.filter(created_at__date__gte=date_from)
    
    if date_to:
        transactions = transactions.filter(created_at__date__lte=date_to)
    
    transactions = transactions.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'accounts': user_accounts,
        'transaction_types': Transaction.TRANSACTION_TYPES,
        'filters': {
            'account': account_filter,
            'type': transaction_type,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'customer/transaction_history.html', context)

@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'customer/change_password.html', {'form': form})

@login_required
def profile_settings(request):
    """Profile settings and preferences"""
    try:
        transaction_limits = UserTransactionLimit.objects.get(user=request.user)
    except UserTransactionLimit.DoesNotExist:
        transaction_limits = UserTransactionLimit.objects.create(user=request.user)
    
    # Calculate usage percentages
    daily_transfer_percentage = 0
    daily_withdrawal_percentage = 0
    
    if transaction_limits.daily_transfer_limit > 0:
        daily_transfer_percentage = (transaction_limits.current_daily_transfers / transaction_limits.daily_transfer_limit) * 100
    
    if transaction_limits.daily_withdrawal_limit > 0:
        daily_withdrawal_percentage = (transaction_limits.current_daily_withdrawals / transaction_limits.daily_withdrawal_limit) * 100
    
    # Get user's ATM cards
    atm_cards = ATMCard.objects.filter(account__customer=request.user)
    
    # Get registered devices (if implemented)
    from .models import DeviceRegistration
    devices = DeviceRegistration.objects.filter(user=request.user)
    
    context = {
        'transaction_limits': transaction_limits,
        'daily_transfer_percentage': round(daily_transfer_percentage, 1),
        'daily_withdrawal_percentage': round(daily_withdrawal_percentage, 1),
        'atm_cards': atm_cards,
        'devices': devices,
    }
    return render(request, 'customer/profile_settings.html', context)


@login_required
def financial_summary(request):
    """Financial summary dashboard"""
    user_accounts = BankAccount.objects.filter(customer=request.user)
    
    # Account summaries
    total_balance = user_accounts.aggregate(Sum('balance'))['balance__sum'] or Decimal('0.00')
    
    # Recent transactions (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_transactions = Transaction.objects.filter(
        account__in=user_accounts,
        created_at__gte=thirty_days_ago
    )
    
    # Transaction summaries
    total_credits = recent_transactions.filter(
        transaction_type__in=['deposit', 'transfer', 'interest_credit', 'loan_disbursement']
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    total_debits = recent_transactions.filter(
        transaction_type__in=['withdrawal', 'bill_payment', 'airtime_purchase', 'fee_charge']
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    
    # Active loans
    active_loans = Loan.objects.filter(borrower=request.user, status='active')
    total_loan_balance = active_loans.aggregate(
        Sum('outstanding_principal')
    )['outstanding_principal__sum'] or Decimal('0.00')
    
    # Monthly spending by category (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_spending = []
    
    for i in range(6):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_total = Transaction.objects.filter(
            account__in=user_accounts,
            transaction_type__in=['withdrawal', 'bill_payment', 'airtime_purchase'],
            created_at__gte=month_start,
            created_at__lte=month_end
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        monthly_spending.append({
            'month': month_start.strftime('%b %Y'),
            'amount': float(month_total)
        })
    
    monthly_spending.reverse()
    
    context = {
        'accounts': user_accounts,
        'total_balance': total_balance,
        'total_credits': total_credits,
        'total_debits': total_debits,
        'active_loans': active_loans,
        'total_loan_balance': total_loan_balance,
        'recent_transactions': recent_transactions[:10],
        'monthly_spending_data': json.dumps(monthly_spending),
    }
    return render(request, 'customer/financial_summary.html', context)

@login_required
def notifications(request):
    """Customer notifications"""
    if request.method == 'POST' and 'mark_read' in request.POST:
        notification_id = request.POST.get('notification_id')
        if notification_id:
            try:
                notification = Notification.objects.get(id=notification_id, user=request.user)
                notification.is_read = True
                notification.read_at = timezone.now()
                notification.save()
                return JsonResponse({'status': 'success'})
            except Notification.DoesNotExist:
                return JsonResponse({'status': 'error'})
    
    # Get notifications with pagination
    notifications_list = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read if requested
    if request.GET.get('mark_all_read'):
        notifications_list.update(is_read=True, read_at=timezone.now())
        messages.success(request, 'All notifications marked as read.')
        return redirect('notifications')
    
    paginator = Paginator(notifications_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Count unread notifications
    unread_count = notifications_list.filter(is_read=False).count()
    
    context = {
        'page_obj': page_obj,
        'unread_count': unread_count,
    }
    return render(request, 'customer/notifications.html', context)

@login_required
def account_statements(request):
    """Account statements list and generation"""
    user_accounts = BankAccount.objects.filter(customer=request.user)
    
    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        
        if account_id and from_date and to_date:
            try:
                account = BankAccount.objects.get(id=account_id, customer=request.user)
                from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
                
                # Check if statement already exists
                existing_statement = AccountStatement.objects.filter(
                    account=account,
                    from_date=from_date,
                    to_date=to_date
                ).first()
                
                if existing_statement:
                    messages.info(request, 'Statement already exists for this period.')
                else:
                    # Create new statement record (actual PDF generation would be handled separately)
                    statement = AccountStatement.objects.create(
                        account=account,
                        statement_date=timezone.now().date(),
                        from_date=from_date,
                        to_date=to_date,
                        opening_balance=Decimal('0.00'),  # Calculate actual opening balance
                        closing_balance=account.balance,
                        is_generated=False
                    )
                    messages.success(request, 'Statement request submitted successfully!')
                
                return redirect('account_statements')
                
            except (ValueError, BankAccount.DoesNotExist):
                messages.error(request, 'Invalid data provided.')
    
    # Get existing statements
    statements = AccountStatement.objects.filter(
        account__in=user_accounts
    ).order_by('-created_at')
    
    paginator = Paginator(statements, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'accounts': user_accounts,
        'page_obj': page_obj,
    }
    return render(request, 'customer/account_statements.html', context)

@login_required
def download_statement(request, statement_id):
    """Download account statement (placeholder for actual PDF generation)"""
    try:
        statement = AccountStatement.objects.get(
            id=statement_id,
            account__customer=request.user
        )
        
        if statement.statement_file:
            # Return the actual file
            response = HttpResponse(statement.statement_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="statement_{statement.account.account_number}_{statement.from_date}_{statement.to_date}.pdf"'
            return response
        else:
            messages.error(request, 'Statement file not yet generated.')
            return redirect('account_statements')
            
    except AccountStatement.DoesNotExist:
        messages.error(request, 'Statement not found.')
        return redirect('account_statements')



# admin_views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *

def is_admin(user):
    return user.is_authenticated and user.user_type == 'admin'



# Analytics
@login_required
@user_passes_test(is_admin)
def analytics(request):
    # Transaction analytics
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    
    daily_transactions = Transaction.objects.filter(
        created_at__date__gte=last_30_days
    ).extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('day')
    
    transaction_by_type = Transaction.objects.values('transaction_type').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    context = {
        'daily_transactions': list(daily_transactions),
        'transaction_by_type': list(transaction_by_type),
    }
    return render(request, 'admin/analytics.html', context)

# User Management Views
@login_required
@user_passes_test(is_admin)
def user_list(request):
    user_type = request.GET.get('type', 'all')
    search = request.GET.get('search', '')
    
    users = User.objects.all()
    
    if user_type != 'all':
        users = users.filter(user_type=user_type)
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone_number__icontains=search)
        )
    
    paginator = Paginator(users, 25)
    page = request.GET.get('page')
    users = paginator.get_page(page)
    
    context = {
        'users': users,
        'user_type': user_type,
        'search': search,
    }
    return render(request, 'admin/users/list.html', context)

@login_required
@user_passes_test(is_admin)
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    accounts = BankAccount.objects.filter(customer=user)
    recent_transactions = Transaction.objects.filter(account__customer=user).order_by('-created_at')[:10]
    
    context = {
        'user': user,
        'accounts': accounts,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'admin/users/detail.html', context)

# KYC Management
@login_required
@user_passes_test(is_admin)
def kyc_management(request):
    status_filter = request.GET.get('status', 'all')
    search = request.GET.get('search', '')
    
    kyc_documents = KYCDocument.objects.select_related('user').all()
    
    if status_filter != 'all':
        kyc_documents = kyc_documents.filter(status=status_filter)
    
    if search:
        kyc_documents = kyc_documents.filter(
            Q(user__username__icontains=search) |
            Q(document_number__icontains=search)
        )
    
    paginator = Paginator(kyc_documents, 25)
    page = request.GET.get('page')
    kyc_documents = paginator.get_page(page)
    
    context = {
        'kyc_documents': kyc_documents,
        'status_filter': status_filter,
        'search': search,
    }
    return render(request, 'admin/kyc/list.html', context)

# Account Management
@login_required
@user_passes_test(is_admin)
def account_list(request):
    account_type = request.GET.get('type', 'all')
    status = request.GET.get('status', 'all')
    search = request.GET.get('search', '')
    
    accounts = BankAccount.objects.select_related('customer', 'account_type', 'branch').all()
    
    if account_type != 'all':
        accounts = accounts.filter(account_type__code=account_type)
    
    if status != 'all':
        accounts = accounts.filter(status=status)
    
    if search:
        accounts = accounts.filter(
            Q(account_number__icontains=search) |
            Q(customer__username__icontains=search)
        )
    
    paginator = Paginator(accounts, 25)
    page = request.GET.get('page')
    accounts = paginator.get_page(page)
    
    context = {
        'accounts': accounts,
        'account_type': account_type,
        'status': status,
        'search': search,
    }
    return render(request, 'admin/accounts/list.html', context)

# Transaction Management
@login_required
@user_passes_test(is_admin)
def transaction_list(request):
    transaction_type = request.GET.get('type', 'all')
    status = request.GET.get('status', 'all')
    channel = request.GET.get('channel', 'all')
    search = request.GET.get('search', '')
    
    transactions = Transaction.objects.select_related('account', 'account__customer').all()
    
    if transaction_type != 'all':
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if status != 'all':
        transactions = transactions.filter(status=status)
    
    if channel != 'all':
        transactions = transactions.filter(channel=channel)
    
    if search:
        transactions = transactions.filter(
            Q(transaction_id__icontains=search) |
            Q(reference_number__icontains=search) |
            Q(account__account_number__icontains=search)
        )
    
    paginator = Paginator(transactions, 25)
    page = request.GET.get('page')
    transactions = paginator.get_page(page)
    
    context = {
        'transactions': transactions,
        'transaction_type': transaction_type,
        'status': status,
        'channel': channel,
        'search': search,
    }
    return render(request, 'admin/transactions/list.html', context)

# Loan Management
@login_required
@user_passes_test(is_admin)
def loan_applications(request):
    status = request.GET.get('status', 'all')
    search = request.GET.get('search', '')
    
    applications = LoanApplication.objects.select_related('applicant', 'loan_type').all()
    
    if status != 'all':
        applications = applications.filter(status=status)
    
    if search:
        applications = applications.filter(
            Q(application_id__icontains=search) |
            Q(applicant__username__icontains=search)
        )
    
    paginator = Paginator(applications, 25)
    page = request.GET.get('page')
    applications = paginator.get_page(page)
    
    context = {
        'applications': applications,
        'status': status,
        'search': search,
    }
    return render(request, 'admin/loans/applications.html', context)

@login_required
@user_passes_test(is_admin)
def active_loans(request):
    loans = Loan.objects.select_related('borrower', 'loan_type').filter(status='active')
    
    paginator = Paginator(loans, 25)
    page = request.GET.get('page')
    loans = paginator.get_page(page)
    
    context = {'loans': loans}
    return render(request, 'admin/loans/active.html', context)

# Branch Management
@login_required
@user_passes_test(is_admin)
def branch_list(request):
    branches = Branch.objects.all()
    
    paginator = Paginator(branches, 25)
    page = request.GET.get('page')
    branches = paginator.get_page(page)
    
    context = {'branches': branches}
    return render(request, 'admin/branches/list.html', context)

# ATM Management
@login_required
@user_passes_test(is_admin)
def atm_list(request):
    atms = ATMMachine.objects.select_related('branch').all()
    
    paginator = Paginator(atms, 25)
    page = request.GET.get('page')
    atms = paginator.get_page(page)
    
    context = {'atms': atms}
    return render(request, 'admin/atms/list.html', context)

# Reports
@login_required
@user_passes_test(is_admin)
def financial_reports(request):
    today = timezone.now().date()
    
    # Daily summary
    daily_transactions = Transaction.objects.filter(
        created_at__date=today,
        status='completed'
    ).aggregate(
        total_amount=Sum('amount'),
        total_count=Count('id')
    )
    
    # Monthly summary
    monthly_transactions = Transaction.objects.filter(
        created_at__date__gte=today.replace(day=1),
        status='completed'
    ).aggregate(
        total_amount=Sum('amount'),
        total_count=Count('id')
    )
    
    context = {
        'daily_transactions': daily_transactions,
        'monthly_transactions': monthly_transactions,
    }
    return render(request, 'admin/reports/financial.html', context)

@login_required
@user_passes_test(is_admin)
def operational_reports(request):
    # System statistics
    stats = {
        'total_users': User.objects.count(),
        'active_accounts': BankAccount.objects.filter(status='active').count(),
        'pending_kyc': KYCDocument.objects.filter(status='pending').count(),
        'active_loans': Loan.objects.filter(status='active').count(),
        'online_atms': ATMMachine.objects.filter(status='online').count(),
    }
    
    context = {'stats': stats}
    return render(request, 'admin/reports/operational.html', context)

# Support
@login_required
@user_passes_test(is_admin)
def support_tickets(request):
    status = request.GET.get('status', 'all')
    priority = request.GET.get('priority', 'all')
    
    tickets = SupportTicket.objects.select_related('customer').all()
    
    if status != 'all':
        tickets = tickets.filter(status=status)
    
    if priority != 'all':
        tickets = tickets.filter(priority=priority)
    
    paginator = Paginator(tickets, 25)
    page = request.GET.get('page')
    tickets = paginator.get_page(page)
    
    context = {
        'tickets': tickets,
        'status': status,
        'priority': priority,
    }
    return render(request, 'admin/support/tickets.html', context)

# System Settings
@login_required
@user_passes_test(is_admin)
def system_settings(request):
    configurations = SystemConfiguration.objects.all()
    
    context = {'configurations': configurations}
    return render(request, 'admin/system/settings.html', context)

@login_required
@user_passes_test(is_admin)
def fee_structure(request):
    fees = FeeStructure.objects.filter(is_active=True)
    
    context = {'fees': fees}
    return render(request, 'admin/system/fees.html', context)

@login_required
@user_passes_test(is_admin)
def audit_trail(request):
    audits = AuditTrail.objects.select_related('user').order_by('-timestamp')[:100]
    
    context = {'audits': audits}
    return render(request, 'admin/system/audit.html', context)

# Security Events
@login_required
@user_passes_test(is_admin)
def security_events(request):
    severity = request.GET.get('severity', 'all')
    
    events = SecurityEvent.objects.select_related('user').all()
    
    if severity != 'all':
        events = events.filter(severity=severity)
    
    paginator = Paginator(events, 25)
    page = request.GET.get('page')
    events = paginator.get_page(page)
    
    context = {
        'events': events,
        'severity': severity,
    }
    return render(request, 'admin/security/events.html', context)