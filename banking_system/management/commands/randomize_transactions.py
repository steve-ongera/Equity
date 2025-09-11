import random
from datetime import timedelta, datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from banking_system.models import Transaction


class Command(BaseCommand):
    help = "Randomize created_at and processed_at for Transactions within last 30 days"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        start_date = now - timedelta(days=30)

        transactions = Transaction.objects.all()
        total = transactions.count()
        self.stdout.write(f"Found {total} transactions... Updating dates.")

        for txn in transactions:
            # Pick a random number of days/hours/minutes ago
            random_days = random.randint(0, 30)
            random_seconds = random.randint(0, 86400)  # up to 24h
            random_datetime = start_date + timedelta(days=random_days, seconds=random_seconds)

            txn.created_at = random_datetime
            # Ensure processed_at is after created_at
            txn.processed_at = random_datetime + timedelta(
                minutes=random.randint(1, 120)
            )

            txn.save(update_fields=["created_at", "processed_at"])

        self.stdout.write(self.style.SUCCESS("✅ Transaction dates randomized successfully."))
