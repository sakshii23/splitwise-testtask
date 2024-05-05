# urls.py
from django.urls import path
from .views import GroupAPIView, Expenses, Reminder, Settlement

urlpatterns = [
    path('create_group/', GroupAPIView.as_view(), name='create_group'),
    path('fetch-groups', GroupAPIView.as_view(), name='fetch-group'),
    path('fetch-groups/<str:group_id>', GroupAPIView.as_view(), name='fetch-group-detail'),

    path('add-expense/', Expenses.as_view(), name='add-expense'),
    path('fetch-expenses', Expenses.as_view(), name='fetch-expenses'),
    path('fetch-expenses/<str:expense_id>', Expenses.as_view(), name='fetch-expense-detail'),

    path('debit-reminder/', Reminder.as_view(), name='debit-reminder'),
    path('settle/', Settlement.as_view(), name='settle-dues'),
]
