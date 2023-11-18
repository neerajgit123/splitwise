from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum,Q

class User(AbstractUser):
    username = models.CharField(max_length = 50, blank = True, null = True, unique = True)
    mobile_number = models.CharField(max_length = 10, unique=True)

    def __str__(self):
        return "{}".format(self.email)
    
    def calculate_balances(self):
        # Calculate the total expenses paid by the user
        total_expenses_paid = self.expenses_paid.aggregate(total=Sum('amount'))['total'] or 0

        # Calculate the total shares in expenses where the user participated
        total_shares = self.expense_shares.aggregate(total=Sum('share'))['total'] or 0
        # Calculate the net balance for the user
        net_balance = total_expenses_paid - total_shares
        print(net_balance)
        # Calculate balances between the user and other users
        balances = []
        for other_user in User.objects.exclude(id=self.id):
            # Calculate the user's balance with each other user
            diff = self.calculate_balance_with_user(other_user)
            if diff<0:

                balances.append(f"{self.username} owes {other_user.username} : {-diff}")
            elif diff>0:
                balances.append(f"{other_user.username} owes {self.username} : {diff}")
            else:
                balances.append(f"{other_user.username} owes {self.username} : {diff}")
        return balances, net_balance

    def calculate_balance_with_user(self, other_user):
        # Calculate the user's balance with a specific other user
        total_expenses_paid_to_other_user = 0
        for i in self.expenses_paid.all():
            total_expenses_paid_to_other_user +=i.expense_shares.filter(user=other_user).aggregate(total=Sum('share'))['total'] or 0
        total_expenses_shared_with_other_user = 0
        for i in other_user.expenses_paid.all():
            total_expenses_shared_with_other_user +=i.expense_shares.filter(user=self).aggregate(total=Sum('share'))['total'] or 0
        # Calculate the balance with the other user

        balance = total_expenses_paid_to_other_user - total_expenses_shared_with_other_user

        return round(balance, 2)

    def get_passbook_entries(self):
        # Get expenses where the user either paid or had a share
        expenses = Expense.objects.filter(Q(user_paid=self) | Q(expense_shares__user=self)).distinct()
        passbook_entries = []

        for expense in expenses:
            entry = {
                'expense_id':expense.expense_id,
                'description': expense.description,
                'amount': expense.amount,
                'expense_type': expense.expense_type,
                'date': expense.created_at,
                'shares': [],
            }

            if expense.user_paid == self:
                entry['shares'].append({
                    'user_id': self.id,
                    'share': expense.amount,  # User paid the full amount
                })
            else:
                # User shared in this expense
                shares = expense.expense_shares.filter(user=self)
                for share in shares:
                    entry['shares'].append({
                        'user_id': share.user.id,
                        'share': share.share,
                    })
            passbook_entries.append(entry)

        return passbook_entries

    

class Expense(models.Model):
    EQUAL = 'EQUAL'
    EXACT = 'EXACT'
    PERCENT = 'PERCENT'

    EXPENSE_TYPES = [
        (EQUAL, 'Equal'),
        (EXACT, 'Exact'),
        (PERCENT, 'Percent'),
    ]

    expense_id = models.AutoField(primary_key=True)
    user_paid = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses_paid')
    description = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_type = models.CharField(max_length=10, choices=EXPENSE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

class ExpenseShare(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="expense_shares")
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE,related_name="expense_shares")
    share = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)