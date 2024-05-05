from .models import Group, GroupMember, Expense, ExpenseSplit
from users.models import User
import expenses.messages as app_messages

from django.db.models import Sum
from typing import Union
from rest_framework import status
from rest_framework.response import Response
from .utils import send_email_notification
from celery import shared_task
from django.conf import settings


def response_helper(success: bool, message: str, status: status, data: Union[dict, list] = None):
    """
    Helper for making response body.
    @TODO : Need to create view base class with this function which will catch exception & return response. \
    @TODO : Eliminating need of calling it manually
    """
    return Response(
        {"success": success, "message": message, "data": data}, status=status
    )


def fetch_user_groups(request: object, group_id: Union[str, int] = None) -> object:
    """
    Helper to fetch user groups
    """
    try:

        if group_id:
            groups = Group.objects.get(id=group_id)
        else:
            member = request.user
            groups = [i.group for i in GroupMember.objects.filter(member=member)]
    except Exception as e:
        groups = None

    return groups


def fetch_user_expense(request: object, expense_id: Union[str, int] = None) -> object:
    """
    Helper to get user expenses.
    """
    try:
        if expense_id:
            expenses = Expense.objects.get(id=expense_id)
        else:
            expence_user = request.user
            expenses = [i.expense for i in ExpenseSplit.objects.filter(expense_user=expence_user)]
    except Exception as e:
        print(str(e))
        expenses = None

    return expenses


def fetch_group_expenses(group: object, request: object) -> tuple:
    """
    Helper to fetch expenses for a group
    """
    member = request.user
    owed_expenses = ExpenseSplit.objects.filter(expense__group=group, expense__expense_by=member).aggregate(
        total_balance_outstanding=Sum('balance_outstanding')).get("total_balance_outstanding", 0)
    borrowed_expenses = ExpenseSplit.objects.filter(expense__group=group).exclude(expense__expense_by=member).aggregate(
        total_balance_outstanding=Sum('balance_outstanding')).get("total_balance_outstanding", 0)
    return owed_expenses, borrowed_expenses


# expense data helpers
def fetch_expense_split(expense: object, request: object) -> tuple:
    """
    Helper to fetch expense data for a user
    """
    member = request.user
    borrowed_expense = ExpenseSplit.objects.filter(expense=expense, expense_user=member, balance_outstanding__gt=0)
    owed_expense_split = ExpenseSplit.objects.filter(expense=expense, balance_outstanding__gt=0).exclude(
        expense_user=member)

    return owed_expense_split, borrowed_expense


def fetch_owed_exp_breakup(owed_expenses: object) -> list:
    """
    Helper to group/aggregate owed expenses data
    """
    owed_exp_details = []
    for debt in owed_expenses:
        exp = {
            "name": debt.expense_user.username,
            "amount": str(debt.balance_outstanding)
        }
        owed_exp_details.append(exp)
    return owed_exp_details


def fetch_borrowed_exp_breakup(borrowed_expenses: object) -> list:
    """
    Helper to group/aggregate borrowed expenses data
    """
    borrowed_exp_details = []
    for debt in borrowed_expenses:
        exp = {
            "name": debt.expense_user.username,
            "amount": str(debt.balance_outstanding)
        }
        borrowed_exp_details.append(exp)
    return borrowed_exp_details


def notify_user_about_debit(lender: User, user_id: Union[str, int]) -> bool:
    """
    Helper to send due pending notification to a friend
    """
    try:
        user = User.objects.get(id=user_id)
        owed_amt = ExpenseSplit.objects.filter(
            expense__expense_by=lender,
            expense_user__id=user_id
        ).aggregate(
            total_balance_outstanding=Sum('balance_outstanding')).get("total_balance_outstanding", 0)
        if not owed_amt:
            raise Exception("All expenses are paid")

        subject = app_messages.DEBIT_REMINDER_MAIL_SUBJECT
        message = app_messages.EXPENSE_RE3MINDER_MAIL_BODY.format(
            user=user.username.capitalize(),
            amount=round(owed_amt, 2),
            lender=lender.username.capitalize()
        )
        send_email_notification.apply_async(kwargs=dict(email=user.email, subject=subject, message=message))
        return True
    except Exception as e:
        print(f"ERROR IN SENDING REMINDER : {str(e)}")
        return False


def settle_expenses(expense_ids: list, user: User) -> tuple:
    """
    Helper function to settle expenses/dues
    """
    try:
        ExpenseSplit.objects.filter(expense__id__in=expense_ids, expense_user=user).update(
            balance_outstanding=0,
            status="Paid"
        )
        return True, "Expense Settled Successfully"
    except Exception as e:
        print(f"ERROR IN SETTLING EXPENSES : {str(e)}")
        return False, str(e)


@shared_task(bind=True, queue=settings.NOTIFICATION_QUEUE)
def update_expense_status(self, **kwargs):
    expenses = kwargs.get("expenses")
    for expense_id in expenses:
        if not ExpenseSplit.objects.filter(expense__id=expense_id, status="Pending",
                                           balance_outstanding__gt=0).exists():
            expense_obj = Expense.objects.get(id=expense_id)
            expense_obj.status = "Paid"
            expense_obj.save()
    return True
