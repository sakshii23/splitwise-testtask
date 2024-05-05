from rest_framework import serializers
from users.models import Friends, User
from .models import Group, GroupMember, Expense, ExpenseSplit
import expenses.constants as app_constants
import expenses.messages as app_messages


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['group_name', 'description']

    def create(self, validated_data):
        group = Group.objects.create(**validated_data)
        return group


class GroupMemberSerializer(serializers.ModelSerializer):
    member = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False))

    class Meta:
        model = GroupMember
        fields = ['group', 'member']

    def __init__(self, *args, **kwargs):
        context_data = kwargs.pop('context', {})
        self.owner_id = context_data.get('owner_id')

        super(GroupMemberSerializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        members_data = validated_data.pop('member', [])
        group = validated_data.pop('group')

        for member in members_data:
            is_owner = False
            if self.owner_id == member.id:
                is_owner = True
            group_member = GroupMember.objects.create(group=group, member=member, is_owner=is_owner)
        return group_member


class ExpenseSplitSerializer(serializers.ModelSerializer):
    split_value = serializers.CharField(write_only=True, allow_null=True)

    class Meta:
        model = ExpenseSplit
        fields = ['split_value', 'split_type', 'expense_user', 'status']


class ExpenseSerializer(serializers.ModelSerializer):
    split_breakup = ExpenseSplitSerializer(many=True, write_only=True)
    balance_amt = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Expense
        fields = ['name', 'balance_amt', 'expense_by', 'split_breakup', 'group']

    def validate(self, data):
        split_breakup = data.get('split_breakup', [])
        balance_amt = data.get('balance_amt')

        split_type_set = set(item['split_type'] for item in split_breakup)
        split_values = [float(item.get('split_value')) for item in split_breakup if item.get('split_value')]
        print(split_type_set)
        if len(split_type_set) > 1:
            raise serializers.ValidationError(app_messages.MULTIPLE_SPLIT_TYPE)
        if split_values:
            if app_constants.SplitType.PERCENTAGE.value  in split_type_set:
                if sum(split_values) != 100:
                    raise serializers.ValidationError(app_messages.PERCENTAGE_SUM_MISMATCH)
            else:
                if sum(split_values) != balance_amt:
                    raise serializers.ValidationError(
                        app_messages.EXACT_AMT_MISMATCH_ERROR)
        else:
            no_of_users = len(split_breakup)
            split_value = round(balance_amt / no_of_users, 2)
            difference = balance_amt - split_value * no_of_users
            for idx, row in enumerate(split_breakup):
                if idx == 1:
                    row["split_value"] = split_value + difference
                else:
                    row["split_value"] = split_value

        return data

    def create(self, validated_data):
        split_breakup_data = validated_data.pop('split_breakup')
        balance_amt = float(validated_data.get('balance_amt'))
        expense = Expense.objects.create(**validated_data)

        for split_data in split_breakup_data:
            split_value = float(split_data.pop('split_value'))
            if split_data['split_type'] == app_constants.SplitType.PERCENTAGE.value:
                amount = round((split_value / 100) * balance_amt, 2)
            else:
                amount = split_value

            balance_outstanding = amount
            if split_data.get("status") == app_constants.SplitExpenseStatus.PAID.value:
                balance_outstanding = 0
            split_breakup_row = ExpenseSplit(expense=expense, amount=amount, balance_outstanding=balance_outstanding,
                                             **split_data)
            split_breakup_row.save()

        return expense
