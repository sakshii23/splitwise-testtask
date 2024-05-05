from rest_framework.views import APIView
from rest_framework import status
from .serializers import (
    GroupSerializer,
    GroupMemberSerializer,
    ExpenseSerializer
)
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
import expenses.helpers as helper


class GroupAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id=None):
        groups = helper.fetch_user_groups(request, group_id)
        if not groups:
            return helper.response_helper(
                success=False,
                message="No data Found",
                data=[],
                status=status.HTTP_400_BAD_REQUEST
            )
        if not group_id:
            result = []
            for group in groups:
                owed_expenses, borrowed_expenses = helper.fetch_group_expenses(group, request)
                result.append(
                    {
                        "group_name": group.group_name,
                        "group_id": group.id,
                        "owed_expenses": owed_expenses if owed_expenses else 0,
                        "borrowed_expenses": borrowed_expenses if borrowed_expenses else 0
                    }
                )
        else:
            owed_expenses, borrowed_expenses = helper.fetch_group_expenses(groups, request)
            result = {
                "group_name": groups.group_name,
                "group_id": groups.id,
                "owed_expenses": owed_expenses if owed_expenses else 0,
                "borrowed_expenses": borrowed_expenses if borrowed_expenses else 0

            }
        return helper.response_helper(
            success=True,
            message="Groups data Found",
            data=result,
            status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        request_data = request.data.copy()
        serializer = GroupSerializer(data=request_data)
        if serializer.is_valid():
            group = serializer.save()
            request_data['group'] = group.id
            request_data['member'].append(request.user.id)

            member_serializer = GroupMemberSerializer(data=request_data, context={"owner_id": request.user.id})
            if member_serializer.is_valid():
                member_serializer.save()
            else:
                print(member_serializer.errors)
            return helper.response_helper(
                success=True,
                message="Group Created",
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        return helper.response_helper(
            success=False,
            message=serializer.errors,
            data=[],
            status=status.HTTP_400_BAD_REQUEST
        )


class Expenses(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, expense_id=None):

        expenses = helper.fetch_user_expense(request, expense_id)
        if not expenses:
            return helper.response_helper(
                success=False,
                message="No data Found",
                data=[],
                status=status.HTTP_400_BAD_REQUEST
            )
        if expense_id:
            owed_expenses, borrowed_expenses = helper.fetch_expense_split(expenses, request)
            result = {"expense_name": expenses.name, "expense_id": expenses.id}
            result["owed_expenses"] = helper.fetch_owed_exp_breakup(owed_expenses)
            result["borrowed_expenses"] = helper.fetch_borrowed_exp_breakup(borrowed_expenses)
        else:
            result = []
            for expense in expenses:
                owed_expenses, borrowed_expenses = helper.fetch_expense_split(expense, request)
                exp_dict = {"expense_name": expense.name, "expense_id": expense.id}
                exp_dict["owed_expenses"] = helper.fetch_owed_exp_breakup(owed_expenses)
                exp_dict["borrowed_expenses"] = helper.fetch_borrowed_exp_breakup(borrowed_expenses)
                result.append(exp_dict)

        return helper.response_helper(
            success=True,
            message="Expenses data Found",
            data=result,
            status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        request_data = request.data.copy()
        request_data["expense_by"] = request.user.id
        serializer = ExpenseSerializer(data=request_data)
        if serializer.is_valid():
            expense = serializer.save()
            return helper.response_helper(
                success=True,
                message="Expense Added",
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        return helper.response_helper(
            success=False,
            message=serializer.errors,
            data=[],
            status=status.HTTP_400_BAD_REQUEST
        )


class Reminder(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        user_id = data.get("user_id")
        lender = request.user
        try:
            helper.notify_user_about_debit(lender, user_id)
            return helper.response_helper(success=True, message="User notified about dues", status=status.HTTP_200_OK)
        except Exception as e:
            return helper.response_helper(success=False, message=f"Failed to send reminder : {str(e)}",
                                          status=status.HTTP_400_BAD_REQUEST)


class Settlement(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        expense_ids = request.data.get("expenses")
        success, message = helper.settle_expenses(expense_ids, request.user)

        if success:
            helper.update_expense_status.apply_async(kwargs=dict(expenses=expense_ids))
        return helper.response_helper(
            success=success,
            message=message,
            status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST
        )
