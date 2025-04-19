from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import csv
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

with app.app_context():
    db.create_all()

def generate_spending_chart(expenses):
    if not expenses:
        return None
    try:
        df = pd.DataFrame([(pd.to_datetime(e.date), float(e.amount)) for e in expenses], 
                         columns=['date', 'amount'])
        df['month'] = df['date'].dt.to_period('M')
        monthly = df.groupby('month')['amount'].sum().reset_index()
        monthly['month'] = monthly['month'].astype(str)
        
        plt.figure(figsize=(10, 5))
        plt.plot(monthly['month'], monthly['amount'], marker='o')
        plt.title('Monthly Spending')
        plt.xlabel('Month')
        plt.ylabel('Amount ($)')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        
        img = BytesIO()
        plt.savefig(img, format='png', dpi=100)
        img.seek(0)
        plt.close()
        return base64.b64encode(img.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Error generating spending chart: {e}")
        return None

def generate_category_chart(expenses):
    if not expenses:
        return None
    try:
        df = pd.DataFrame([(e.category, float(e.amount)) for e in expenses], 
                         columns=['category', 'amount'])
        category_totals = df.groupby('category')['amount'].sum()
        
        plt.figure(figsize=(8, 8))
        plt.pie(category_totals, 
               labels=category_totals.index, 
               autopct='%1.1f%%',
               startangle=90)
        plt.title('Spending by Category')
        plt.tight_layout()
        
        img = BytesIO()
        plt.savefig(img, format='png', dpi=100)
        img.seek(0)
        plt.close()
        return base64.b64encode(img.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Error generating category chart: {e}")
        return None

@app.route('/')
def home():
    return render_template('home.html', user_name="Dharun")

@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form['description']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        
        new_expense = Expense(
            amount=amount,
            category=category,
            description=description,
            date=date
        )
        
        db.session.add(new_expense)
        db.session.commit()
        
        return redirect(url_for('view_expenses'))
    
    return render_template('add_expense.html')

@app.route('/expenses')
def view_expenses():
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Expense.query
    
    if category and category != 'All':
        query = query.filter(Expense.category == category)
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(Expense.date >= start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Expense.date <= end_date)
    
    categories = db.session.query(Expense.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    expenses = query.order_by(Expense.date.desc()).all()
    total = sum(exp.amount for exp in expenses)
    
    return render_template(
        'view_expenses.html',
        expenses=expenses,
        categories=categories,
        total=total,
        selected_category=category or 'All',
        start_date=start_date,
        end_date=end_date
    )

@app.route('/dashboard')
def dashboard():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Expense.query
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(Expense.date >= start_date)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Expense.date <= end_date)
    
    expenses = query.all()
    
    if not expenses:
        return render_template('dashboard.html', 
                           monthly_chart=None,
                           category_chart=None,
                           monthly_data=[],
                           category_data=[])
    
    monthly_chart = generate_spending_chart(expenses)
    category_chart = generate_category_chart(expenses)
    
    df = pd.DataFrame([(pd.to_datetime(e.date), e.category, float(e.amount)) 
                      for e in expenses], 
                     columns=['date', 'category', 'amount'])
    
    df['month'] = df['date'].dt.to_period('M')
    monthly_data = df.groupby('month')['amount'].sum().reset_index()
    monthly_data['month'] = monthly_data['month'].astype(str)
    
    category_data = df.groupby('category')['amount'].sum().reset_index()
    
    return render_template('dashboard.html',
                         monthly_chart=monthly_chart,
                         category_chart=category_chart,
                         monthly_data=monthly_data.to_dict('records'),
                         category_data=category_data.to_dict('records'))

@app.route('/export')
def export_expenses():
    expenses = Expense.query.all()
    output = BytesIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Category', 'Amount', 'Description'])
    
    for exp in expenses:
        writer.writerow([
            exp.date.strftime('%Y-%m-%d'),
            exp.category,
            exp.amount,
            exp.description
        ])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=expenses.csv'
    response.headers['Content-type'] = 'text/csv'
    return response

if __name__ == '__main__':
    app.run(debug=True)