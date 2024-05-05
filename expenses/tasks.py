# tasks.py
from celery import shared_task
from django.db.models import Sum
from expenses.models import ExpenseSplit
import expenses.messages as app_messages
from .utils import send_email_notification
from django.conf import settings


@shared_task(queue=settings.NOTIFICATION_QUEUE)
def weeekly_notification_task():
    expense_splits = ExpenseSplit.objects.filter(
        balance_outstanding__gt=0
    ).values(
        'expense__expense_by',
        'expense__expense_by__username',
        'expense_user__email',
        'expense_user__username'
    ).annotate(
        total_amount=Sum('amount')
    )

    for split in expense_splits:
        try:
            lender = split["expense__expense_by__username"]
            borrower_email = split['expense_user__email']
            borrower_name = split["expense_user__username"]
            amount = split['total_amount']

            subject = app_messages.DEBIT_REMINDER_MAIL_SUBJECT
            message = app_messages.EXPENSE_RE3MINDER_MAIL_BODY.format(
                user=borrower_name.capitalize(),
                amount=round(amount, 2),
                lender=lender.capitalize()
            )
            send_email_notification.apply_async(kwargs=dict(email=borrower_email, subject=subject, message=message))
        except Exception as e:
            print(str(e))
        return True
