from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from split.views import UserCreate,UserListView,ExpenseListView,UserPassbookView,UserBalacesView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User-related URLs
    path('users/register/', UserCreate.as_view(), name='user-registration'),
    path('user/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/', UserListView.as_view(), name='user-list'),

    # Expense-related URLs
    path('expenses/', ExpenseListView.as_view(), name='expense-list'),

    # User balance and passbook URLs
    path('user_balances/', UserBalacesView.as_view(), name='user-balances'),
    path('passbook/', UserPassbookView.as_view(), name='user-passbook'),
]
