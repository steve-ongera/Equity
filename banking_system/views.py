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
