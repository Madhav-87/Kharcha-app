from django.core.management.base import BaseCommand, CommandError

from apps.payments.reconciliation import reconcile_stale_payments


class Command(BaseCommand):
    help = "Move stale unresolved UPI payment attempts to unknown for follow-up."

    def add_arguments(self, parser):
        parser.add_argument("--older-than-minutes", type=int, default=20)
        parser.add_argument("--batch-size", type=int, default=500)

    def handle(self, *args, **options):
        minutes = options["older_than_minutes"]
        batch_size = options["batch_size"]
        if minutes < 1 or batch_size < 1:
            raise CommandError("Both older-than-minutes and batch-size must be positive.")
        count = reconcile_stale_payments(older_than_minutes=minutes, batch_size=batch_size)
        self.stdout.write(self.style.SUCCESS(f"Moved {count} stale payment(s) to unknown."))
