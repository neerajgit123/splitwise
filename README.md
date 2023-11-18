# splitwise

## Introduction
This is a Django project that utilizes Docker for containerization and Celery for distributed task processing. Follow the instructions below to set up the project locally.

## Prerequisites
Make sure you have the following installed on your machine:
- Docker
- Docker Compose

## Getting Started
1. Clone the repository:
   ```bash
   git clone https://github.com/neerajgit123/splitwise

2. Navigate to the project directory:
   ```bash
    cd your-django-project

3. Build and start the Docker containers:
   ```bash
    docker-compose up --build

4. Apply migrations and create a superuser:
   ```bash
    docker-compose exec web python manage.py migrate
    docker-compose exec web python manage.py createsuperuser



Register User

http://127.0.0.1:8000/users/register/ #POST by form data
```
{
    "first_name":"jhon"  ,
    "last_name": "black",
    "email": "user4@gmail.com",
    "mobile_number":"42006657898",
    "username":"jk",
    "password":"test2@gmail.com"

}
```

Login User

http://127.0.0.1:8000/user/login/ #POST by form data
```
{
    "username":"jk",
    "password":"test2@gmail.com"

}
```

All APIs are authenticated


Users Lists

http://127.0.0.1:8000/users #GET


Create Expense

http://127.0.0.1:8000/expenses/ #POST by form data
```
{
    "description": "breakfast",
    "amount": 1000,
    "expense_type": "EQUAL",
    "selected_user": [
        {
            "user_id": 1
        },
        {
            "user_id": 3
        },
        {
            "user_id": 4
        }        
    ]
}
```

All users balance with current user

http://127.0.0.1:8000/user_balances/ #Get


Get All transactions

http://127.0.0.1:8000/passbook/ #Get
