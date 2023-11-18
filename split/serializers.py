from split.models import User, Expense, ExpenseShare
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model =User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'mobile_number']


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'


class ExpenseShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseShare
        fields = '__all__'


class UserPassbookSerializer(serializers.ModelSerializer):
    shares = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = ('expense_id','description', 'amount', 'expense_type', 'created_at', 'shares')

    def get_shares(self, obj):
        shares = ExpenseShare.objects.filter(expense=obj["expense_id"])
        share_data = [{'user_id': share.user.id, 'share': share.share} for share in shares]
        return share_data