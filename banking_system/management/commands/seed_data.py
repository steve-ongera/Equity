#!/usr/bin/env python
"""
Seed data script for Banking System
Place this file in: banking_system/management/commands/seed_data.py

Run with: python manage.py seed_data
"""

import sys
import django
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from decimal import Decimal
from datetime import datetime, date, timedelta
import random
from faker import Faker
import secrets
import string

from banking_system.models import (
    User, KYCDocument, Branch, BankAgent, AccountType, BankAccount,
    ATMMachine, Transaction, InterestCalculation, AccountStatement,
    ForexRate, Notification, SecurityEvent, AuditTrail, SystemConfiguration,
    FeeStructure, SupportTicket, DeviceRegistration, UserTransactionLimit,
    StandingOrder, ATMCard, LoanType, LoanApplication, Loan, LoanPayment,
    MobileBankingSession, BillPaymentService, BillPayment, CardlessWithdrawal,
    AgentTransactionLimit
)

fake = Faker()

class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        self.clear_data()
        
        # Create data in order of dependencies
        self.create_users()
        self.create_branches()
        self.create_account_types()
        self.create_bank_agents()
        self.create_bank_accounts()
        self.create_atm_machines()
        self.create_atm_cards()
        self.create_transactions()
        self.create_kyc_documents()
        self.create_user_transaction_limits()
        self.create_forex_rates()
        self.create_fee_structures()
        self.create_system_configurations()
        self.create_loan_types()
        self.create_loan_applications()
        self.create_loans()
        self.create_bill_payment_services()
        self.create_bill_payments()
        self.create_standing_orders()
        self.create_notifications()
        self.create_security_events()
        self.create_support_tickets()
        self.create_device_registrations()
        self.create_cardless_withdrawals()
        self.create_agent_transaction_limits()
        self.create_interest_calculations()
        self.create_account_statements()
        self.create_audit_trails()
        self.create_mobile_banking_sessions()
        self.create_loan_payments()
        
        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))

    def clear_data(self):
        """Clear existing data (optional)"""
        self.stdout.write('Clearing existing data...')
        # Clear in reverse order of dependencies
        Transaction.objects.all().delete()
        ATMCard.objects.all().delete()
        BankAccount.objects.all().delete()
        BankAgent.objects.all().delete()
        ATMMachine.objects.all().delete()
        Branch.objects.all().delete()
        User.objects.all().delete()
        AccountType.objects.all().delete()

    def create_users(self):
        """Create different types of users"""
        self.stdout.write('Creating users...')
        
        # Kenyan cities for addresses
        kenyan_cities = [
            'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 
            'Thika', 'Machakos', 'Meru', 'Nyeri', 'Kericho'
        ]
        
        # Create 3 admins
        admin_users = []
        admin_names = [
            ('John', 'Kimani', 'john.kimani@bank.co.ke'),
            ('Grace', 'Wanjiku', 'grace.wanjiku@bank.co.ke'),
            ('Peter', 'Otieno', 'peter.otieno@bank.co.ke')
        ]
        
        for first_name, last_name, email in admin_names:
            user = User.objects.create(
                username=f"{first_name.lower()}.{last_name.lower()}",
                first_name=first_name,
                last_name=last_name,
                email=email,
                user_type='admin',
                phone_number=f"+254{random.randint(700000000, 799999999)}",
                national_id=f"{random.randint(10000000, 99999999)}",
                date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=50),
                address=fake.address(),
                city=random.choice(kenyan_cities),
                postal_code=f"{random.randint(10000, 99999)}",
                occupation="Bank Administrator",
                employer="Our Bank",
                monthly_income=Decimal(random.randint(80000, 150000)),
                kyc_status='verified',
                is_staff=True,
                is_superuser=True,
                password=make_password('admin123')
            )
            admin_users.append(user)

        # Create 20 bank staff
        staff_users = []
        for i in range(20):
            first_name = fake.first_name()
            last_name = fake.last_name()
            user = User.objects.create(
                username=f"staff_{i+1}",
                first_name=first_name,
                last_name=last_name,
                email=f"{first_name.lower()}.{last_name.lower()}@bank.co.ke",
                user_type='staff',
                phone_number=f"+254{random.randint(700000000, 799999999)}",
                national_id=f"{random.randint(10000000, 99999999)}",
                date_of_birth=fake.date_of_birth(minimum_age=22, maximum_age=55),
                address=fake.address(),
                city=random.choice(kenyan_cities),
                postal_code=f"{random.randint(10000, 99999)}",
                occupation=random.choice(['Bank Teller', 'Customer Service Rep', 'Loan Officer', 'Branch Manager']),
                employer="Our Bank",
                monthly_income=Decimal(random.randint(40000, 100000)),
                kyc_status='verified',
                is_staff=True,
                password=make_password('staff123')
            )
            staff_users.append(user)

        # Create 50 agents
        agent_users = []
        kenyan_first_names = [
            'James', 'Mary', 'John', 'Grace', 'David', 'Susan', 'Michael', 'Jane',
            'Peter', 'Rose', 'Joseph', 'Margaret', 'Daniel', 'Agnes', 'Samuel',
            'Catherine', 'Francis', 'Joyce', 'Paul', 'Ann', 'Moses', 'Elizabeth'
        ]
        kenyan_last_names = [
            'Mwangi', 'Wanjiku', 'Kimani', 'Nyong\'o', 'Otieno', 'Wanyama',
            'Kipchoge', 'Chebet', 'Kiptoo', 'Jeptoo', 'Kamau', 'Njeri',
            'Kiprotich', 'Chepkemei', 'Mutua', 'Muthoni', 'Ochieng', 'Achieng'
        ]
        
        for i in range(50):
            first_name = random.choice(kenyan_first_names)
            last_name = random.choice(kenyan_last_names)
            user = User.objects.create(
                username=f"agent_{i+1}",
                first_name=first_name,
                last_name=last_name,
                email=f"{first_name.lower()}.{last_name.lower()}.agent{i+1}@gmail.com",
                user_type='agent',
                phone_number=f"+254{random.randint(700000000, 799999999)}",
                national_id=f"{random.randint(10000000, 99999999)}",
                date_of_birth=fake.date_of_birth(minimum_age=21, maximum_age=60),
                address=fake.address(),
                city=random.choice(kenyan_cities),
                postal_code=f"{random.randint(10000, 99999)}",
                occupation="Banking Agent",
                employer="Self Employed",
                monthly_income=Decimal(random.randint(25000, 80000)),
                kyc_status='verified',
                password=make_password('agent123')
            )
            agent_users.append(user)

        # Create 300 customers
        customer_users = []
        occupations = [
            'Teacher', 'Nurse', 'Driver', 'Mechanic', 'Shop Owner', 'Farmer',
            'Accountant', 'Engineer', 'Doctor', 'Lawyer', 'Chef', 'Tailor',
            'Security Guard', 'Cleaner', 'Sales Person', 'Student', 'Retired'
        ]
        
        for i in range(300):
            first_name = random.choice(kenyan_first_names)
            last_name = random.choice(kenyan_last_names)
            user = User.objects.create(
                username=f"customer_{i+1}",
                first_name=first_name,
                last_name=last_name,
                email=f"{first_name.lower()}.{last_name.lower()}.{i+1}@gmail.com",
                user_type='customer',
                phone_number=f"+254{random.randint(700000000, 799999999)}",
                national_id=f"{random.randint(10000000, 99999999)}",
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=75),
                address=fake.address(),
                city=random.choice(kenyan_cities),
                postal_code=f"{random.randint(10000, 99999)}",
                occupation=random.choice(occupations),
                employer=fake.company() if random.choice([True, False]) else "Self Employed",
                monthly_income=Decimal(random.randint(15000, 200000)),
                kyc_status=random.choices(['verified', 'pending', 'rejected'], weights=[80, 15, 5])[0],
                password=make_password('customer123')
            )
            customer_users.append(user)

        self.stdout.write(f'Created {len(admin_users)} admins, {len(staff_users)} staff, {len(agent_users)} agents, {len(customer_users)} customers')

    def create_branches(self):
        """Create bank branches"""
        self.stdout.write('Creating branches...')
        
        branch_data = [
            {'name': 'Nairobi Main Branch', 'city': 'Nairobi', 'county': 'Nairobi'},
            {'name': 'Westlands Branch', 'city': 'Nairobi', 'county': 'Nairobi'},
            {'name': 'Mombasa Branch', 'city': 'Mombasa', 'county': 'Mombasa'},
            {'name': 'Kisumu Branch', 'city': 'Kisumu', 'county': 'Kisumu'},
            {'name': 'Nakuru Branch', 'city': 'Nakuru', 'county': 'Nakuru'},
            {'name': 'Eldoret Branch', 'city': 'Eldoret', 'county': 'Uasin Gishu'},
            {'name': 'Thika Branch', 'city': 'Thika', 'county': 'Kiambu'},
            {'name': 'Machakos Branch', 'city': 'Machakos', 'county': 'Machakos'},
            {'name': 'Meru Branch', 'city': 'Meru', 'county': 'Meru'},
            {'name': 'Nyeri Branch', 'city': 'Nyeri', 'county': 'Nyeri'},
        ]
        
        staff_users = list(User.objects.filter(user_type='staff'))
        
        for i, data in enumerate(branch_data):
            branch = Branch.objects.create(
                name=data['name'],
                branch_code=f"BR{i+1:03d}",
                address=fake.address(),
                city=data['city'],
                county=data['county'],
                phone_number=f"+254{random.randint(200000000, 299999999)}",
                email=f"info.{data['name'].lower().replace(' ', '')}@bank.co.ke",
                manager=random.choice(staff_users) if staff_users else None,
                opening_time="08:00:00",
                closing_time="17:00:00"
            )

        self.stdout.write(f'Created {len(branch_data)} branches')

    def create_account_types(self):
        """Create account types"""
        self.stdout.write('Creating account types...')
        
        account_types_data = [
            {
                'name': 'Savings Account',
                'code': 'SAV',
                'minimum_balance': Decimal('1000.00'),
                'monthly_maintenance_fee': Decimal('50.00'),
                'interest_rate': Decimal('3.5000'),
                'withdrawal_limit_daily': Decimal('40000.00'),
                'withdrawal_limit_monthly': Decimal('500000.00'),
            },
            {
                'name': 'Current Account',
                'code': 'CUR',
                'minimum_balance': Decimal('5000.00'),
                'monthly_maintenance_fee': Decimal('200.00'),
                'interest_rate': Decimal('0.0000'),
                'withdrawal_limit_daily': Decimal('100000.00'),
                'withdrawal_limit_monthly': Decimal('2000000.00'),
                'allows_overdraft': True,
            },
            {
                'name': 'Fixed Deposit',
                'code': 'FD',
                'minimum_balance': Decimal('10000.00'),
                'monthly_maintenance_fee': Decimal('0.00'),
                'interest_rate': Decimal('7.5000'),
                'withdrawal_limit_daily': Decimal('0.00'),
                'withdrawal_limit_monthly': Decimal('0.00'),
            },
            {
                'name': 'Student Account',
                'code': 'STU',
                'minimum_balance': Decimal('100.00'),
                'monthly_maintenance_fee': Decimal('0.00'),
                'interest_rate': Decimal('2.0000'),
                'withdrawal_limit_daily': Decimal('10000.00'),
                'withdrawal_limit_monthly': Decimal('50000.00'),
            },
        ]
        
        for data in account_types_data:
            AccountType.objects.create(**data)

        self.stdout.write(f'Created {len(account_types_data)} account types')

    def create_bank_agents(self):
        """Create bank agents"""
        self.stdout.write('Creating bank agents...')
        
        agent_users = User.objects.filter(user_type='agent')
        branches = list(Branch.objects.all())
        
        business_types = [
            'Mobile Money Shop', 'General Store', 'Pharmacy', 'Hardware Store',
            'Supermarket', 'Electronics Shop', 'Clothing Store', 'Stationery Shop'
        ]
        
        for i, user in enumerate(agent_users):
            agent = BankAgent.objects.create(
                user=user,
                agent_code=f"AG{i+1:05d}",
                branch=random.choice(branches),
                business_name=f"{user.first_name}'s {random.choice(business_types)}",
                business_address=user.address,
                business_phone=user.phone_number,
                license_number=f"LIC{random.randint(100000, 999999)}",
                daily_limit=Decimal(random.choice([300000, 500000, 750000])),
                monthly_limit=Decimal(random.choice([5000000, 10000000, 15000000])),
                current_daily_total=Decimal('0.00'),
                current_monthly_total=Decimal('0.00')
            )

        self.stdout.write(f'Created {agent_users.count()} bank agents')

    def create_bank_accounts(self):
        """Create bank accounts for customers"""
        self.stdout.write('Creating bank accounts...')
        
        customers = User.objects.filter(user_type='customer', kyc_status='verified')
        account_types = list(AccountType.objects.all())
        branches = list(Branch.objects.all())
        agents = list(BankAgent.objects.all())
        
        accounts_created = 0
        for customer in customers:
            # Each customer gets 1-3 accounts
            num_accounts = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
            
            for i in range(num_accounts):
                account_type = random.choice(account_types)
                initial_balance = Decimal(random.randint(1000, 500000))
                
                account = BankAccount.objects.create(
                    customer=customer,
                    account_type=account_type,
                    branch=random.choice(branches),
                    created_by_agent=random.choice(agents) if random.choice([True, False]) else None,
                    balance=initial_balance,
                    available_balance=initial_balance,
                    is_primary=(i == 0),  # First account is primary
                    pin_hash=make_password('1234')  # Default PIN
                )
                accounts_created += 1

        self.stdout.write(f'Created {accounts_created} bank accounts')

    def create_atm_machines(self):
        """Create ATM machines"""
        self.stdout.write('Creating ATM machines...')
        
        branches = list(Branch.objects.all())
        locations = [
            'City Center Mall', 'Airport Terminal', 'Shopping Center', 'Hospital',
            'University Campus', 'Bus Station', 'Market Square', 'Office Complex'
        ]
        
        atm_count = 0
        for branch in branches:
            # Each branch has 2-5 ATMs
            num_atms = random.randint(2, 5)
            
            for i in range(num_atms):
                atm = ATMMachine.objects.create(
                    atm_id=f"ATM{branch.branch_code}{i+1:02d}",
                    location_name=f"{random.choice(locations)} - {branch.city}",
                    address=fake.address(),
                    city=branch.city,
                    county=branch.county,
                    latitude=Decimal(random.uniform(-4.5, 4.5)),  # Kenya latitude range
                    longitude=Decimal(random.uniform(33.5, 42.0)),  # Kenya longitude range
                    branch=branch,
                    status=random.choices(['online', 'offline', 'maintenance'], weights=[85, 10, 5])[0],
                    cash_available=Decimal(random.randint(500000, 2000000)),
                    max_cash_capacity=Decimal('5000000.00'),
                    daily_withdrawal_limit=Decimal('40000.00'),
                    single_withdrawal_limit=Decimal('20000.00'),
                    supports_deposit=random.choice([True, False]),
                    supports_cardless=True,
                )
                atm_count += 1

        self.stdout.write(f'Created {atm_count} ATM machines')

    def create_atm_cards(self):
        """Create ATM cards for accounts"""
        self.stdout.write('Creating ATM cards...')
        
        accounts = BankAccount.objects.filter(account_type__allows_overdraft=False)[:200]  # Cards for first 200 accounts
        agents = list(BankAgent.objects.all())
        
        cards_created = 0
        for account in accounts:
            if random.choice([True, False]):  # 50% of accounts get cards
                card = ATMCard.objects.create(
                    account=account,
                    cardholder_name=f"{account.customer.first_name} {account.customer.last_name}".upper(),
                    card_type='debit',
                    daily_withdrawal_limit=Decimal(random.choice([20000, 40000, 60000])),
                    daily_purchase_limit=Decimal(random.choice([100000, 200000, 300000])),
                    issued_by_agent=random.choice(agents) if random.choice([True, False]) else None,
                )
                cards_created += 1

        self.stdout.write(f'Created {cards_created} ATM cards')

    def create_transactions(self):
        """Create sample transactions"""
        self.stdout.write('Creating transactions...')
        
        accounts = list(BankAccount.objects.all()[:100])  # Use first 100 accounts
        atms = list(ATMMachine.objects.all())
        agents = list(BankAgent.objects.all())
        branches = list(Branch.objects.all())
        
        transaction_types = ['deposit', 'withdrawal', 'transfer', 'bill_payment', 'airtime_purchase']
        channels = ['atm', 'mobile', 'agent', 'branch', 'ussd']
        
        transactions_created = 0
        for account in accounts:
            # Each account gets 5-20 transactions
            num_transactions = random.randint(5, 20)
            current_balance = account.balance
            
            for _ in range(num_transactions):
                transaction_type = random.choice(transaction_types)
                channel = random.choice(channels)
                amount = Decimal(random.randint(100, 50000))
                fee = Decimal(random.randint(0, 100))
                
                # Adjust balance based on transaction type
                if transaction_type in ['withdrawal', 'transfer', 'bill_payment', 'airtime_purchase']:
                    balance_before = current_balance
                    current_balance -= (amount + fee)
                    balance_after = current_balance
                else:  # deposit
                    balance_before = current_balance
                    current_balance += amount
                    balance_after = current_balance
                
                # Create transaction with past dates
                created_date = fake.date_time_between(start_date='-6M', end_date='now')
                
                transaction = Transaction.objects.create(
                    account=account,
                    transaction_type=transaction_type,
                    amount=amount,
                    fee=fee,
                    total_amount=amount + fee if transaction_type != 'deposit' else amount,
                    balance_before=balance_before,
                    balance_after=balance_after,
                    channel=channel,
                    reference_number=f"REF{random.randint(100000, 999999)}",
                    description=f"{transaction_type.title()} via {channel}",
                    status='completed',
                    atm_machine=random.choice(atms) if channel == 'atm' else None,
                    agent=random.choice(agents) if channel == 'agent' else None,
                    branch=random.choice(branches) if channel == 'branch' else None,
                    created_at=created_date,
                    processed_at=created_date
                )
                transactions_created += 1

        self.stdout.write(f'Created {transactions_created} transactions')

    def create_kyc_documents(self):
        """Create KYC documents"""
        self.stdout.write('Creating KYC documents...')
        
        customers = User.objects.filter(user_type='customer')
        staff = list(User.objects.filter(user_type='staff'))
        
        document_types = ['national_id', 'payslip', 'utility_bill', 'bank_statement']
        
        documents_created = 0
        for customer in customers:
            # Each customer has 2-4 KYC documents
            num_docs = random.randint(2, 4)
            selected_types = random.sample(document_types, num_docs)
            
            for doc_type in selected_types:
                KYCDocument.objects.create(
                    user=customer,
                    document_type=doc_type,
                    document_number=f"DOC{random.randint(100000, 999999)}",
                    issue_date=fake.date_between(start_date='-5y', end_date='-1y'),
                    expiry_date=fake.date_between(start_date='+1y', end_date='+10y') if doc_type != 'utility_bill' else None,
                    status='verified' if customer.kyc_status == 'verified' else random.choice(['pending', 'rejected']),
                    verified_by=random.choice(staff) if customer.kyc_status == 'verified' else None,
                    verified_at=fake.date_time_between(start_date='-1y', end_date='now') if customer.kyc_status == 'verified' else None
                )
                documents_created += 1

        self.stdout.write(f'Created {documents_created} KYC documents')

    def create_user_transaction_limits(self):
        """Create transaction limits for users"""
        self.stdout.write('Creating user transaction limits...')
        
        customers = User.objects.filter(user_type='customer')
        
        for customer in customers:
            UserTransactionLimit.objects.create(
                user=customer,
                daily_transfer_limit=Decimal(random.choice([500000, 1000000, 2000000])),
                daily_withdrawal_limit=Decimal(random.choice([50000, 100000, 150000])),
                monthly_transfer_limit=Decimal(random.choice([5000000, 10000000, 20000000])),
                single_transaction_limit=Decimal(random.choice([200000, 500000, 1000000])),
                current_daily_transfers=Decimal(random.randint(0, 50000)),
                current_daily_withdrawals=Decimal(random.randint(0, 20000)),
                current_monthly_transfers=Decimal(random.randint(0, 500000)),
            )

        self.stdout.write(f'Created transaction limits for {customers.count()} customers')

    def create_forex_rates(self):
        """Create forex rates"""
        self.stdout.write('Creating forex rates...')
        
        currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD']
        
        for currency in currencies:
            # Create rates for the last 30 days
            for i in range(30):
                date = datetime.now() - timedelta(days=i)
                base_rate = random.uniform(100, 150) if currency == 'USD' else random.uniform(50, 200)
                
                ForexRate.objects.create(
                    base_currency='KES',
                    target_currency=currency,
                    buy_rate=Decimal(base_rate * 0.98),
                    sell_rate=Decimal(base_rate * 1.02),
                    mid_rate=Decimal(base_rate),
                    effective_date=date
                )

        self.stdout.write(f'Created forex rates for {len(currencies)} currencies')

    def create_fee_structures(self):
        """Create fee structures"""
        self.stdout.write('Creating fee structures...')
        
        fee_data = [
            ('atm_withdrawal_on_us', Decimal('15.00'), Decimal('0.0000')),
            ('atm_withdrawal_off_us', Decimal('35.00'), Decimal('0.0000')),
            ('mobile_transfer_own', Decimal('0.00'), Decimal('1.0000')),
            ('mobile_transfer_other', Decimal('25.00'), Decimal('1.5000')),
            ('agent_deposit', Decimal('0.00'), Decimal('0.0000')),
            ('agent_withdrawal', Decimal('30.00'), Decimal('0.0000')),
            ('card_issuance', Decimal('500.00'), Decimal('0.0000')),
            ('statement_request', Decimal('50.00'), Decimal('0.0000')),
        ]
        
        for transaction_type, fixed_fee, percentage_fee in fee_data:
            FeeStructure.objects.create(
                transaction_type=transaction_type,
                fixed_fee=fixed_fee,
                percentage_fee=percentage_fee,
                minimum_fee=Decimal('0.00'),
                maximum_fee=Decimal('1000.00') if percentage_fee > 0 else None,
                effective_from=datetime.now() - timedelta(days=365)
            )

        self.stdout.write(f'Created {len(fee_data)} fee structures')

    def create_system_configurations(self):
        """Create system configurations"""
        self.stdout.write('Creating system configurations...')
        
        configs = [
            ('daily_transaction_limit', '1000000.00', 'transaction', 'Default daily transaction limit'),
            ('max_pin_attempts', '3', 'security', 'Maximum PIN attempts before card blocking'),
            ('session_timeout', '300', 'security', 'Session timeout in seconds'),
            ('sms_notifications', 'true', 'notification', 'Enable SMS notifications'),
            ('email_notifications', 'true', 'notification', 'Enable email notifications'),
            ('maintenance_mode', 'false', 'general', 'System maintenance mode'),
        ]
        
        admin_user = User.objects.filter(user_type='admin').first()
        
        for key, value, config_type, description in configs:
            SystemConfiguration.objects.create(
                key=key,
                value=value,
                config_type=config_type,
                description=description,
                created_by=admin_user
            )

        self.stdout.write(f'Created {len(configs)} system configurations')

    def create_loan_types(self):
        """Create loan types"""
        self.stdout.write('Creating loan types...')
        
        loan_types_data = [
            {
                'name': 'Personal Loan',
                'code': 'PL',
                'description': 'Unsecured personal loan for various needs',
                'min_amount': Decimal('10000.00'),
                'max_amount': Decimal('1000000.00'),
                'min_tenure_months': 6,
                'max_tenure_months': 60,
                'interest_rate': Decimal('14.5000'),
                'processing_fee_percentage': Decimal('2.0000'),
                'requires_guarantor': False,
                'requires_collateral': False,
                'min_income_requirement': Decimal('30000.00'),
                'is_instant': False,
            },
            {
                'name': 'Business Loan',
                'code': 'BL',
                'description': 'Loan for business expansion and working capital',
                'min_amount': Decimal('50000.00'),
                'max_amount': Decimal('10000000.00'),
                'min_tenure_months': 12,
                'max_tenure_months': 84,
                'interest_rate': Decimal('16.0000'),
                'processing_fee_percentage': Decimal('3.0000'),
                'requires_guarantor': True,
                'requires_collateral': True,
                'min_income_requirement': Decimal('100000.00'),
                'is_instant': False,
            },
            {
                'name': 'Instant Mobile Loan',
                'code': 'IML',
                'description': 'Quick mobile loan for emergencies',
                'min_amount': Decimal('500.00'),
                'max_amount': Decimal('50000.00'),
                'min_tenure_months': 1,
                'max_tenure_months': 6,
                'interest_rate': Decimal('18.0000'),
                'processing_fee_percentage': Decimal('0.0000'),
                'requires_guarantor': False,
                'requires_collateral': False,
                'min_income_requirement': Decimal('15000.00'),
                'is_instant': True,
            },
            {
                'name': 'Asset Finance',
                'code': 'AF',
                'description': 'Loan for purchasing vehicles, machinery, equipment',
                'min_amount': Decimal('100000.00'),
                'max_amount': Decimal('20000000.00'),
                'min_tenure_months': 12,
                'max_tenure_months': 96,
                'interest_rate': Decimal('15.5000'),
                'processing_fee_percentage': Decimal('2.5000'),
                'requires_guarantor': False,
                'requires_collateral': True,
                'min_income_requirement': Decimal('50000.00'),
                'is_instant': False,
            },
        ]
        
        for data in loan_types_data:
            LoanType.objects.create(**data)

        self.stdout.write(f'Created {len(loan_types_data)} loan types')

    def create_loan_applications(self):
        """Create loan applications"""
        self.stdout.write('Creating loan applications...')
        
        customers = User.objects.filter(user_type='customer', kyc_status='verified')[:100]  # First 100 verified customers
        loan_types = list(LoanType.objects.all())
        staff = list(User.objects.filter(user_type='staff'))
        
        applications_created = 0
        for customer in customers:
            # 30% of customers have loan applications
            if random.random() < 0.3:
                accounts = list(customer.accounts.all())
                if accounts:
                    loan_type = random.choice(loan_types)
                    requested_amount = Decimal(random.randint(
                        int(loan_type.min_amount), 
                        min(int(loan_type.max_amount), int(customer.monthly_income * 10))
                    ))
                    
                    status = random.choices(
                        ['pending', 'approved', 'rejected', 'under_review'],
                        weights=[30, 40, 20, 10]
                    )[0]
                    
                    application = LoanApplication.objects.create(
                        applicant=customer,
                        account=random.choice(accounts),
                        loan_type=loan_type,
                        requested_amount=requested_amount,
                        approved_amount=requested_amount * Decimal('0.9') if status == 'approved' else None,
                        tenure_months=random.randint(loan_type.min_tenure_months, loan_type.max_tenure_months),
                        purpose=random.choice(['Business expansion', 'Education', 'Medical expenses', 'Home improvement', 'Emergency']),
                        monthly_income=customer.monthly_income,
                        employment_details=f"Working as {customer.occupation} at {customer.employer}",
                        status=status,
                        credit_score=random.randint(300, 850),
                        risk_rating=random.choice(['Low', 'Medium', 'High']),
                        processed_by=random.choice(staff) if status in ['approved', 'rejected'] else None,
                        rejection_reason=random.choice(['Insufficient income', 'Poor credit history', 'Incomplete documentation']) if status == 'rejected' else '',
                        processed_at=fake.date_time_between(start_date='-3M', end_date='now') if status in ['approved', 'rejected'] else None
                    )
                    applications_created += 1

        self.stdout.write(f'Created {applications_created} loan applications')

    def create_loans(self):
        """Create active loans from approved applications"""
        self.stdout.write('Creating loans...')
        
        approved_applications = LoanApplication.objects.filter(status='approved')
        
        loans_created = 0
        for application in approved_applications:
            # Calculate monthly installment (simple calculation for demo)
            principal = application.approved_amount
            monthly_rate = application.loan_type.interest_rate / Decimal('100') / Decimal('12')
            tenure = application.tenure_months
            
            # Simple EMI calculation
            if monthly_rate > 0:
                emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure) / (((1 + monthly_rate) ** tenure) - 1)
            else:
                emi = principal / tenure
                
            disbursement_date = fake.date_time_between(start_date='-2M', end_date='now')
            first_payment_date = disbursement_date.date() + timedelta(days=30)
            maturity_date = first_payment_date + timedelta(days=30 * tenure)
            
            loan = Loan.objects.create(
                application=application,
                borrower=application.applicant,
                account=application.account,
                loan_type=application.loan_type,
                principal_amount=principal,
                interest_rate=application.loan_type.interest_rate,
                tenure_months=tenure,
                monthly_installment=emi.quantize(Decimal('0.01')),
                outstanding_principal=principal,
                outstanding_interest=Decimal('0.00'),
                total_paid=Decimal('0.00'),
                disbursement_date=disbursement_date,
                first_payment_date=first_payment_date,
                maturity_date=maturity_date,
                status='active',
                days_in_arrears=random.randint(0, 30)
            )
            loans_created += 1

        self.stdout.write(f'Created {loans_created} loans')

    def create_bill_payment_services(self):
        """Create bill payment services"""
        self.stdout.write('Creating bill payment services...')
        
        services_data = [
            {'name': 'Kenya Power (KPLC)', 'code': 'KPLC', 'category': 'Utilities', 'fee': Decimal('25.00')},
            {'name': 'Safaricom Postpaid', 'code': 'SAF_POST', 'category': 'Telecom', 'fee': Decimal('0.00')},
            {'name': 'Airtel Money', 'code': 'AIRTEL', 'category': 'Telecom', 'fee': Decimal('10.00')},
            {'name': 'Nairobi Water', 'code': 'NRB_WATER', 'category': 'Utilities', 'fee': Decimal('30.00')},
            {'name': 'DStv', 'code': 'DSTV', 'category': 'Entertainment', 'fee': Decimal('50.00')},
            {'name': 'Zuku', 'code': 'ZUKU', 'category': 'Internet', 'fee': Decimal('40.00')},
            {'name': 'NHIF', 'code': 'NHIF', 'category': 'Insurance', 'fee': Decimal('0.00')},
            {'name': 'NSSF', 'code': 'NSSF', 'category': 'Social Security', 'fee': Decimal('0.00')},
        ]
        
        for data in services_data:
            BillPaymentService.objects.create(**data)

        self.stdout.write(f'Created {len(services_data)} bill payment services')

    def create_bill_payments(self):
        """Create bill payments"""
        self.stdout.write('Creating bill payments...')
        
        accounts = list(BankAccount.objects.all()[:50])  # First 50 accounts
        services = list(BillPaymentService.objects.all())
        channels = ['mobile', 'internet', 'ussd', 'agent']
        
        payments_created = 0
        for account in accounts:
            # Each account has 0-5 bill payments
            num_payments = random.randint(0, 5)
            
            for _ in range(num_payments):
                service = random.choice(services)
                amount = Decimal(random.randint(500, 10000))
                
                payment = BillPayment.objects.create(
                    account=account,
                    service=service,
                    account_number=f"{service.code}{random.randint(100000, 999999)}",
                    amount=amount,
                    fee=service.fee,
                    total_amount=amount + service.fee,
                    status=random.choices(['completed', 'pending', 'failed'], weights=[85, 10, 5])[0],
                    reference_number=f"BP{random.randint(100000, 999999)}",
                    receipt_number=f"RCP{random.randint(100000, 999999)}",
                    channel=random.choice(channels),
                    created_at=fake.date_time_between(start_date='-3M', end_date='now'),
                    processed_at=fake.date_time_between(start_date='-3M', end_date='now')
                )
                payments_created += 1

        self.stdout.write(f'Created {payments_created} bill payments')

    def create_standing_orders(self):
        """Create standing orders"""
        self.stdout.write('Creating standing orders...')
        
        accounts = list(BankAccount.objects.all()[:30])  # First 30 accounts
        
        orders_created = 0
        for account in accounts:
            # 20% of accounts have standing orders
            if random.random() < 0.2:
                amount = Decimal(random.randint(1000, 50000))
                frequency = random.choice(['monthly', 'weekly', 'quarterly'])
                
                start_date = fake.date_between(start_date='-6M', end_date='+1M')
                if frequency == 'monthly':
                    next_execution = start_date + timedelta(days=30)
                elif frequency == 'weekly':
                    next_execution = start_date + timedelta(days=7)
                else:  # quarterly
                    next_execution = start_date + timedelta(days=90)
                
                standing_order = StandingOrder.objects.create(
                    account=account,
                    beneficiary_account_number=f"{random.randint(1000000000, 9999999999)}",
                    beneficiary_name=fake.name(),
                    beneficiary_bank=random.choice(['KCB', 'Equity', 'Standard Chartered', 'Barclays']),
                    amount=amount,
                    frequency=frequency,
                    reference=f"Standing Order - {fake.word()}",
                    start_date=start_date,
                    end_date=fake.date_between(start_date='+1y', end_date='+3y') if random.choice([True, False]) else None,
                    next_execution_date=next_execution,
                    status=random.choices(['active', 'paused', 'cancelled'], weights=[70, 20, 10])[0],
                    execution_count=random.randint(0, 12),
                    failed_count=random.randint(0, 2)
                )
                orders_created += 1

        self.stdout.write(f'Created {orders_created} standing orders')

    def create_notifications(self):
        """Create notifications"""
        self.stdout.write('Creating notifications...')
        
        users = list(User.objects.filter(user_type='customer')[:100])
        transactions = list(Transaction.objects.all()[:50])
        
        notification_types = ['transaction', 'account', 'security', 'promotional']
        channels = ['sms', 'email', 'push', 'in_app']
        
        notifications_created = 0
        for user in users:
            # Each user gets 3-10 notifications
            num_notifications = random.randint(3, 10)
            
            for _ in range(num_notifications):
                notification_type = random.choice(notification_types)
                channel = random.choice(channels)
                
                if notification_type == 'transaction':
                    title = "Transaction Alert"
                    message = f"Your account has been debited with KES {random.randint(100, 10000)}"
                    related_transaction = random.choice(transactions) if transactions else None
                elif notification_type == 'account':
                    title = "Account Update"
                    message = "Your account information has been updated successfully"
                    related_transaction = None
                elif notification_type == 'security':
                    title = "Security Alert"
                    message = "New login detected on your account"
                    related_transaction = None
                else:  # promotional
                    title = "Special Offer"
                    message = "Get a personal loan at reduced interest rates!"
                    related_transaction = None
                
                notification = Notification.objects.create(
                    user=user,
                    notification_type=notification_type,
                    channel=channel,
                    title=title,
                    message=message,
                    status=random.choices(['sent', 'read', 'failed'], weights=[60, 30, 10])[0],
                    related_transaction=related_transaction,
                    is_read=random.choice([True, False]),
                    created_at=fake.date_time_between(start_date='-1M', end_date='now'),
                    sent_at=fake.date_time_between(start_date='-1M', end_date='now'),
                    read_at=fake.date_time_between(start_date='-1M', end_date='now') if random.choice([True, False]) else None
                )
                notifications_created += 1

        self.stdout.write(f'Created {notifications_created} notifications')

    def create_security_events(self):
        """Create security events"""
        self.stdout.write('Creating security events...')
        
        users = list(User.objects.filter(user_type='customer')[:50])
        staff = list(User.objects.filter(user_type='staff'))
        
        event_types = ['login_success', 'login_failed', 'password_change', 'suspicious_transaction']
        severity_levels = ['low', 'medium', 'high']
        
        events_created = 0
        for user in users:
            # Each user gets 1-5 security events
            num_events = random.randint(1, 5)
            
            for _ in range(num_events):
                event_type = random.choice(event_types)
                severity = random.choice(severity_levels)
                
                event = SecurityEvent.objects.create(
                    user=user,
                    event_type=event_type,
                    severity=severity,
                    description=f"{event_type.replace('_', ' ').title()} detected",
                    ip_address=fake.ipv4(),
                    user_agent=fake.user_agent(),
                    location=f"{user.city}, Kenya",
                    device_info=f"{fake.random_element(['Android', 'iOS', 'Windows'])} Device",
                    is_resolved=random.choice([True, False]),
                    resolved_by=random.choice(staff) if random.choice([True, False]) else None,
                    resolution_notes=fake.text(max_nb_chars=200) if random.choice([True, False]) else '',
                    created_at=fake.date_time_between(start_date='-2M', end_date='now'),
                    resolved_at=fake.date_time_between(start_date='-1M', end_date='now') if random.choice([True, False]) else None
                )
                events_created += 1

        self.stdout.write(f'Created {events_created} security events')

    def create_support_tickets(self):
        """Create support tickets"""
        self.stdout.write('Creating support tickets...')
        
        customers = list(User.objects.filter(user_type='customer')[:50])
        staff = list(User.objects.filter(user_type='staff'))
        
        categories = ['account', 'card', 'transaction', 'loan', 'technical', 'general']
        priorities = ['low', 'medium', 'high', 'urgent']
        statuses = ['open', 'in_progress', 'resolved', 'closed']
        
        tickets_created = 0
        for customer in customers:
            # 30% of customers have support tickets
            if random.random() < 0.3:
                category = random.choice(categories)
                
                ticket = SupportTicket.objects.create(
                    customer=customer,
                    category=category,
                    subject=f"{category.title()} Issue - {fake.sentence(nb_words=4)}",
                    description=fake.text(max_nb_chars=500),
                    priority=random.choice(priorities),
                    status=random.choice(statuses),
                    assigned_to=random.choice(staff) if random.choice([True, False]) else None,
                    resolution=fake.text(max_nb_chars=300) if random.choice([True, False]) else '',
                    created_at=fake.date_time_between(start_date='-3M', end_date='now'),
                    resolved_at=fake.date_time_between(start_date='-2M', end_date='now') if random.choice([True, False]) else None
                )
                tickets_created += 1

        self.stdout.write(f'Created {tickets_created} support tickets')

    def create_device_registrations(self):
        """Create device registrations"""
        self.stdout.write('Creating device registrations...')
        
        customers = list(User.objects.filter(user_type='customer')[:100])
        device_types = ['Android', 'iOS', 'Web']
        
        registrations_created = 0
        for customer in customers:
            # Each customer has 1-3 registered devices
            num_devices = random.randint(1, 3)
            
            for i in range(num_devices):
                device_type = random.choice(device_types)
                
                registration = DeviceRegistration.objects.create(
                    user=customer,
                    device_id=f"DEV{random.randint(100000000, 999999999)}",
                    device_name=f"{customer.first_name}'s {device_type} Device {i+1}",
                    device_type=device_type,
                    device_model=fake.random_element(['Samsung Galaxy', 'iPhone 13', 'Huawei P40', 'Chrome Browser']),
                    os_version=fake.random_element(['Android 12', 'iOS 15', 'Windows 10']),
                    app_version=f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                    is_trusted=random.choice([True, False]),
                    is_active=random.choice([True, False]),
                    last_used=fake.date_time_between(start_date='-1M', end_date='now'),
                    registration_ip=fake.ipv4(),
                    created_at=fake.date_time_between(start_date='-6M', end_date='now')
                )
                registrations_created += 1

        self.stdout.write(f'Created {registrations_created} device registrations')

    def create_cardless_withdrawals(self):
        """Create cardless withdrawals"""
        self.stdout.write('Creating cardless withdrawals...')
        
        accounts = list(BankAccount.objects.all()[:30])
        atms = list(ATMMachine.objects.all())
        
        withdrawals_created = 0
        for account in accounts:
            # 20% of accounts have cardless withdrawals
            if random.random() < 0.2:
                amount = Decimal(random.randint(500, 20000))
                status = random.choices(['used', 'expired', 'cancelled', 'active'], weights=[50, 25, 15, 10])[0]
                
                withdrawal = CardlessWithdrawal.objects.create(
                    account=account,
                    amount=amount,
                    recipient_phone=f"+254{random.randint(700000000, 799999999)}",
                    recipient_name=fake.name(),
                    status=status,
                    atm_used=random.choice(atms) if status == 'used' else None,
                    expires_at=datetime.now() + timedelta(hours=24),
                    used_at=fake.date_time_between(start_date='-1M', end_date='now') if status == 'used' else None,
                    created_at=fake.date_time_between(start_date='-1M', end_date='now')
                )
                withdrawals_created += 1

        self.stdout.write(f'Created {withdrawals_created} cardless withdrawals')

    def create_agent_transaction_limits(self):
        """Create agent transaction limits"""
        self.stdout.write('Creating agent transaction limits...')
        
        agents = BankAgent.objects.all()
        
        for agent in agents:
            AgentTransactionLimit.objects.create(
                agent=agent,
                single_deposit_limit=Decimal(random.choice([200000, 300000, 500000])),
                single_withdrawal_limit=Decimal(random.choice([50000, 70000, 100000])),
                daily_transaction_limit=agent.daily_limit,
                monthly_transaction_limit=agent.monthly_limit,
                current_daily_total=Decimal(random.randint(0, 100000)),
                current_monthly_total=Decimal(random.randint(0, 1000000))
            )

        self.stdout.write(f'Created transaction limits for {agents.count()} agents')

    def create_interest_calculations(self):
        """Create interest calculations"""
        self.stdout.write('Creating interest calculations...')
        
        savings_accounts = BankAccount.objects.filter(account_type__interest_rate__gt=0)[:20]
        
        calculations_created = 0
        for account in savings_accounts:
            # Create interest calculations for the last 3 months
            for i in range(90):
                calc_date = date.today() - timedelta(days=i)
                balance = account.balance + Decimal(random.randint(-10000, 10000))
                interest_rate = account.account_type.interest_rate
                daily_rate = interest_rate / Decimal('100') / Decimal('365')
                interest_earned = balance * daily_rate
                
                InterestCalculation.objects.create(
                    account=account,
                    calculation_date=calc_date,
                    balance=balance,
                    interest_rate=interest_rate,
                    interest_earned=interest_earned.quantize(Decimal('0.01')),
                    days_calculated=1,
                    is_credited=random.choice([True, False])
                )
                calculations_created += 1

        self.stdout.write(f'Created {calculations_created} interest calculations')

    def create_account_statements(self):
        """Create account statements"""
        self.stdout.write('Creating account statements...')
        
        accounts = list(BankAccount.objects.all()[:20])
        
        statements_created = 0
        for account in accounts:
            # Create monthly statements for the last 6 months
            for i in range(6):
                end_date = date.today().replace(day=1) - timedelta(days=i*30)
                start_date = end_date - timedelta(days=30)
                
                opening_balance = account.balance + Decimal(random.randint(-50000, 50000))
                closing_balance = account.balance + Decimal(random.randint(-30000, 30000))
                
                statement = AccountStatement.objects.create(
                    account=account,
                    statement_date=end_date,
                    from_date=start_date,
                    to_date=end_date,
                    opening_balance=opening_balance,
                    closing_balance=closing_balance,
                    total_credits=Decimal(random.randint(10000, 100000)),
                    total_debits=Decimal(random.randint(5000, 80000)),
                    is_generated=random.choice([True, False])
                )
                statements_created += 1

        self.stdout.write(f'Created {statements_created} account statements')

    def create_audit_trails(self):
        """Create audit trails"""
        self.stdout.write('Creating audit trails...')
        
        users = list(User.objects.all()[:50])
        actions = ['create', 'update', 'delete', 'view', 'approve', 'reject']
        models = ['BankAccount', 'Transaction', 'User', 'LoanApplication']
        
        trails_created = 0
        for user in users:
            # Each user has 5-15 audit trail entries
            num_trails = random.randint(5, 15)
            
            for _ in range(num_trails):
                action = random.choice(actions)
                model_name = random.choice(models)
                
                trail = AuditTrail.objects.create(
                    user=user,
                    action=action,
                    model_name=model_name,
                    object_id=str(random.randint(1, 1000)),
                    object_repr=f"{model_name} {random.randint(1, 1000)}",
                    changes={'field': 'old_value -> new_value'} if action == 'update' else None,
                    ip_address=fake.ipv4(),
                    user_agent=fake.user_agent(),
                    timestamp=fake.date_time_between(start_date='-3M', end_date='now')
                )
                trails_created += 1

        self.stdout.write(f'Created {trails_created} audit trails')

    def create_mobile_banking_sessions(self):
        """Create mobile banking sessions"""
        self.stdout.write('Creating mobile banking sessions...')
        
        customers = list(User.objects.filter(user_type='customer')[:30])
        channels = ['ussd', 'mobile_app', 'sms']
        
        sessions_created = 0
        for customer in customers:
            # Each customer has 1-3 active or recent sessions
            num_sessions = random.randint(1, 3)
            
            for _ in range(num_sessions):
                channel = random.choice(channels)
                created_time = fake.date_time_between(start_date='-1d', end_date='now')
                expires_time = created_time + timedelta(minutes=random.randint(10, 60))
                
                session = MobileBankingSession.objects.create(
                    session_id=f"SESS{random.randint(100000000, 999999999)}",
                    user=customer,
                    phone_number=customer.phone_number,
                    channel=channel,
                    is_active=random.choice([True, False]),
                    created_at=created_time,
                    expires_at=expires_time
                )
                sessions_created += 1

        self.stdout.write(f'Created {sessions_created} mobile banking sessions')

    def create_loan_payments(self):
        """Create loan payments"""
        self.stdout.write('Creating loan payments...')
        
        loans = Loan.objects.filter(status='active')
        
        payments_created = 0
        for loan in loans:
            # Each loan has 1-12 payments (depending on how long it's been active)
            months_active = min(12, (datetime.now().date() - loan.disbursement_date.date()).days // 30)
            num_payments = random.randint(1, max(1, months_active))
            
            for i in range(num_payments):
                payment_date = loan.disbursement_date + timedelta(days=30*(i+1))
                due_date = loan.first_payment_date + timedelta(days=30*i)
                
                # Split payment into principal and interest
                interest_amount = loan.outstanding_principal * (loan.interest_rate / Decimal('100') / Decimal('12'))
                principal_amount = loan.monthly_installment - interest_amount
                
                payment = LoanPayment.objects.create(
                    loan=loan,
                    amount=loan.monthly_installment,
                    principal_amount=principal_amount.quantize(Decimal('0.01')),
                    interest_amount=interest_amount.quantize(Decimal('0.01')),
                    penalty_amount=Decimal('0.00'),
                    payment_date=payment_date,
                    due_date=due_date,
                    status='completed',
                    payment_channel=random.choice(['mobile', 'branch', 'atm']),
                    reference_number=f"LP{random.randint(100000, 999999)}"
                )
                payments_created += 1

        self.stdout.write(f'Created {payments_created} loan payments')