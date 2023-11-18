from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from split.models import Expense
from django.db import transaction
from split.exceptions import AmountSumMismatchError

User = get_user_model()

class ExpenseAPITest(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='testpassword',
            mobile_number=9999911111
        )
        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpassword',
            mobile_number=9999922222
        )
        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)
        self.user3 = User.objects.create_user(
            username='testuser3',
            password='testpassword',
            mobile_number=9999933333
        )
        self.client3 = APIClient()
        self.client3.force_authenticate(user=self.user3)
        self.user4 = User.objects.create_user(
            username='testuser4',
            password='testpassword',
            mobile_number=9999944444
        )
        self.client4 = APIClient()
        self.client4.force_authenticate(user=self.user4)

    def test_create_equalsplit_expense(self):
        url = reverse('expense-list')
        data = {
            'user_paid': self.user1.id,
            'description': 'Test Expense',
            'amount': 1000.00,
            'expense_type': 'EQUAL',
            "selected_user":[{
                "user_id":self.user1.id,
            },{
                "user_id":self.user2.id,
            },{
                "user_id":self.user3.id,
            },{
                "user_id":self.user4.id,
            }]
        }
        response = self.client1.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)

    def test_create_exactsplit_expense(self):
        url = reverse('expense-list')
        data = {
            'user_paid': self.user1.id,
            'description': 'Test Expense',
            'amount': 1250.00,
            'expense_type': 'EXACT',
            "selected_user":[{
                "user_id":self.user2.id,
                "share":370
            },{
                "user_id":self.user3.id,
                "share":880
            }]
        }
        response = self.client1.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)
    
    def test_wrongsum_of_exactsplit_expense(self):
        url = reverse('expense-list')
        data = {
            'user_paid': self.user1.id,
            'description': 'Test Expense',
            'amount': 1250.00,
            'expense_type': 'EXACT',
            "selected_user":[{
                "user_id":self.user2.id,
                "share":200
            },{
                "user_id":self.user3.id,
                "share":880
            }]
        }
        try:
            with transaction.atomic():
                response = self.client1.post(url, data, format='json')
        except AmountSumMismatchError as e:
            # Check that the exception is raised as expected
            self.assertIn('total sum of shares is not equal to the total amount', str(e))
        # Check that the transaction is rolled back, i.e., the expense is not created
        self.assertEqual(Expense.objects.count(), 0)

    def test_create_percentsplit_expense(self):
        url = reverse('expense-list')
        data = {
            'user_paid': self.user4.id,
            'description': 'Test Expense',
            'amount': 1200.00,
            'expense_type': 'PERCENT',
            "selected_user":[{
                    "user_id":self.user1.id,
                    "share":40
                },{
                    "user_id":self.user2.id,
                    "share":20
                },{
                    "user_id":self.user3.id,
                    "share":20
                },{
                    "user_id":self.user4.id,
                    "share":20
            }]
        }
        response = self.client1.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)
    
    def test_wrongsum_of_percentplit_expense(self):
        url = reverse('expense-list')
        data = {
            'user_paid': self.user1.id,
            'description': 'Test Expense',
            'amount': 1200.00,
            'expense_type': 'PERCENT',
            "selected_user":[{
                    "user_id":self.user1.id,
                    "share":50
                },{
                    "user_id":self.user2.id,
                    "share":20
                },{
                    "user_id":self.user3.id,
                    "share":20
                },{
                    "user_id":self.user4.id,
                    "share":20
            }]
        }
        try:
            with transaction.atomic():
                response = self.client1.post(url, data, format='json')
        except AmountSumMismatchError as e:
            # Check that the exception is raised as expected
            self.assertIn('total sum of percent is not equal to the 100', str(e))
        # Check that the transaction is rolled back, i.e., the expense is not created
        self.assertEqual(Expense.objects.count(), 0)