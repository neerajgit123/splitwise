from rest_framework.views import APIView
from split.serializers import UserSerializer,ExpenseSerializer,ExpenseShareSerializer,UserPassbookSerializer
from rest_framework import status
from rest_framework.response import Response
from split.models import User, Expense
from django.shortcuts import get_object_or_404
from rest_framework import generics
from django.db import transaction
from split.exceptions import MismatchError
from split.tasks import send_mail_when_expense_added
from datetime import timedelta
from celery import current_app
# Create your views here.

class UserCreate(APIView):
    serializer_class = UserSerializer
    permission_classes = ()
    authentication_classes = ()

    def post(self, request, format='json'):
        dict = request.data.copy()
        dict['username'] = request.data.get('username', '').lower()
        dict['email'] = request.data.get('email', '').lower()
        serializer = self.serializer_class(data=dict)
        if serializer.is_valid():
            user = serializer.save()
            p = request.data.get('password')
            if p:
                user.set_password(p)
                user.is_active = True
                user.save()
                return Response({"message": "USER_CREATED_SUCCESS"}, status=status.HTTP_201_CREATED)
            else:
                return Response({"password": ["This field is required"]}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ExpenseListView(APIView):
    serializer_class = ExpenseSerializer

    def post(self,request):
        data = request.data.copy()
        data['user_paid'] = request.user.id
        if len(data['selected_user']) >= 1000:
            return Response({'message':'Each expense can have up to 1000 participants'}, status=status.HTTP_400_BAD_REQUEST)
        elif data['amount'] >= 10000000:
            return Response({'message':'the maximum amount for an expense can go up to INR 1,00,00,000/-'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            serializer= ExpenseSerializer(data=data)
            if serializer.is_valid():
                expense = serializer.save()
                send_mail_when_expense_added.apply_async(kwargs={'expense_id': expense.expense_id},eta=current_app.now() + timedelta(seconds=60))
                if data['expense_type']=="EQUAL":
                    total = len(data['selected_user'])
                    for i in range(len(data['selected_user'])):
                        user = get_object_or_404(User, id=data['selected_user'][i]['user_id'])
                        new = {}
                        new["user"]=user.id 
                        new["expense"]=expense.expense_id

                        new["share"]=round(data['amount']/total, 2)
                        value = str(new["share"]).split('.')[-1]
                        if i == 0 and len(value) == 2 and value[-1]!=0:
                            new["share"] = round(new["share"]+.01, 2)

                        serializerex = ExpenseShareSerializer(data = new)
                        if serializerex.is_valid():
                            serializerex.save()
                        else:
                            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    return Response({"message": "Expense Distributed equally"}, status=status.HTTP_201_CREATED)
                elif data['expense_type']=="EXACT":
                    amount_sum = 0
                    for i in data['selected_user']:
                        user = get_object_or_404(User, id=i['user_id'])
                        new = {}
                        new["user"]=user.id 
                        new["expense"]=expense.expense_id
                        new["share"]= round(i["share"],2)
                        amount_sum += i["share"]
                        serializerex = ExpenseShareSerializer(data = new)
                        if serializerex.is_valid():
                            serializerex.save()
                        else:
                            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    if amount_sum !=data["amount"]:
                        raise MismatchError(" total sum of shares is not equal to the total amount")
                    return Response({"message": "Expense distributed exactly"}, status=status.HTTP_201_CREATED)
                elif data['expense_type']=='PERCENT':
                    percent_sum = 0
                    for i in data['selected_user']:
                        user = get_object_or_404(User, id=i['user_id'])
                        new = {}
                        new["user"]=user.id 
                        new["expense"]=expense.expense_id
                        new["share"]=round(data["amount"]*i["share"]/100, 2)
                        percent_sum +=i["share"]
                        serializerex = ExpenseShareSerializer(data = new)
                        if serializerex.is_valid():
                            serializerex.save()
                        else:
                            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    if percent_sum !=100:
                        raise MismatchError(" total sum of percent is not equal to the 100")
                    return Response({"message": "Expense distributed percent wise"}, status=status.HTTP_201_CREATED)
                else:
                    raise MismatchError("select type from anyone of this EQUAL, EXACT,PERCENT")
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserBalacesView(APIView):
    def get(self,request):
        balances, balance = request.user.calculate_balances()
        return Response({"user_id": request.user.id,"current_balance get form users":balance, "balances": balances}, status=status.HTTP_200_OK)

class UserPassbookView(generics.ListAPIView):
    queryset = Expense.objects.all()
    serializer_class = UserPassbookSerializer

    def list(self, request, *args, **kwargs):
        expenses = request.user.get_passbook_entries()
        serializer = self.serializer_class(expenses, many=True)
        return Response(serializer.data)