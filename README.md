🍽️ FOOD PLAZA

Food Plaza is an online food ordering website developed using Django, Python, HTML, CSS, and Razorpay.  
It allows users to browse food items, add them to the cart, make secure payments, and track their orders.  

🛠️ Tech Stack
- 🐍 Backend: Django, Python  
- 🗄️ Database: SQLite3 or MySQL  
- 🎨 Frontend: HTML, CSS, JavaScript  
- 💳 Payment Gateway: Razorpay 

✨ Features
- 📂 Product listings with categories  
- 🛒 Add to cart and checkout  
- 💳 Razorpay payment integration  
- 👤 User registration and order tracking  
- 🛠️ Admin panel for managing items and orders    

🚀 How to Run

1. Open  pycharm

2.Navigate to the project folder

cd food-plaza

3.Create and activate virtual environment

python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

4.Install dependencies

pip install -r requirements.txt

5.Add Razorpay API keys in settings.py

RAZORPAY_KEY_ID = 'your_test_key_id'
RAZORPAY_KEY_SECRET = 'your_test_key_secret'

6.Run migrations

python manage.py makemigrations
python manage.py migrate

7.Create superuser (optional)

python manage.py createsuperuser

8.Run the development server

python manage.py runserver


9.Open in browser
👉 http://127.0.0.1:8000

👨‍💻 Author

Name: Mahesh Yandrapati

Role: Full Stack Developer

🌐 GitHub: maheshmahesh570
