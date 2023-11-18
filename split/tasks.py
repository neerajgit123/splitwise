from celery import shared_task
from .models import User

from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags
from .models import Expense
from django.db.models import Sum,Q

@shared_task
def send_mail_every_7days():
    user_objs = User.objects.all()
    for obj in user_objs:
        users, balance = calculate_balances(obj)
        to = obj.email
        html_message = render_to_string(
            template_name='weekly_send_email.html',
            context={
                "users": users,
                "total_amount": str(round(balance,2)),
                'user_name': obj.username,
                'past_date': (datetime.now() - timedelta(days=7)).date(),
                'current_date': datetime.now().date()
            }
        )
        subject= "Weekly Balance Update"
        send_email(subject, to,html_message )
        
   

@shared_task
def send_mail_when_expense_added(expense_id):
    expense =  Expense.objects.get(expense_id=expense_id)
    for expense_shares in expense.expense_shares.all():
        to = expense_shares.user.email
        html_message = render_to_string(
        template_name='expense_add_mail.html', context={"user_name":expense_shares.user.username ,
                                                          "expense_title":expense.description,
                                                           "total_amount":str(expense_shares.share) }
        )
        subject= "New Expense Notification"
        send_email(subject, to,html_message )
        
        
def send_email(subject,to,html_message):
    plain_message = strip_tags(html_message)
    send_mail(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [to],
        html_message=html_message,
        )

from datetime import datetime, timedelta



def calculate_balances(self):
    # Calculate the total expenses paid by the user
    total_expenses_paid = self.expenses_paid.filter(created_at__date__gte=(datetime.now() - timedelta(days=7)).date(),created_at__date__lte=datetime.now().date()).aggregate(total=Sum('amount'))['total'] or 0
    

    # Calculate the total shares in expenses where the user participated
    total_shares = self.expense_shares.filter(created_at__date__gte=(datetime.now() - timedelta(days=7)).date(),created_at__date__lte=datetime.now().date()).aggregate(total=Sum('share'))['total'] or 0
    # Calculate the net balance for the user
    
    net_balance = total_expenses_paid - total_shares
    # Calculate balances between the user and other users
    balances = []
    for other_user in User.objects.exclude(id=self.id):
        # Calculate the user's balance with each other user
        diff = calculate_balance_with_user(self, other_user)
        if diff<0:

            balances.append({'user':other_user.username ,'balance': -diff})
        elif diff>0:
            balances.append({'user':other_user.username,'balance':diff})
        else:
            balances.append({'user':other_user.username ,'balance': diff})
    return balances, total_shares

def calculate_balance_with_user(self, other_user):
    # Calculate the user's balance with a specific other user
    total_expenses_paid_to_other_user = 0
    for i in self.expenses_paid.all():
        total_expenses_paid_to_other_user +=i.expense_shares.filter(user=other_user, created_at__date__gte=(datetime.now() - timedelta(days=7)).date(),created_at__date__lte=datetime.now().date()).aggregate(total=Sum('share'))['total'] or 0
    total_expenses_shared_with_other_user = 0
    for i in other_user.expenses_paid.all():
        total_expenses_shared_with_other_user +=i.expense_shares.filter(user=self, created_at__date__gte=(datetime.now() - timedelta(days=7)).date(),created_at__date__lte=datetime.now().date()).aggregate(total=Sum('share'))['total'] or 0
    # Calculate the balance with the other user

    balance = total_expenses_paid_to_other_user - total_expenses_shared_with_other_user

    return round(balance, 2)