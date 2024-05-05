EXPENSE_STATUS_CHOICES = (
    ('Pending', 'Pending'),
    ('Paid', 'Paid'),
)

SPLIT_CHOICES = (
    ('Equal', 'Equal'),
    ('Exact', 'Exact'),
    ('Percentage', 'Percentage'),
)

from enum import Enum


class SplitType(Enum):
    PERCENTAGE = 'Percentage'
    EXACT = 'Exact'
    EQUAL = 'Equal'


class SplitExpenseStatus(Enum):
    PAID = "Paid"
    PENDING = "Pending"
