def generate_spending_chart(expenses):
    """Generate monthly spending line chart"""
    if not expenses:
        return None
        
    try:
        # Create DataFrame with proper datetime conversion
        df = pd.DataFrame([(pd.to_datetime(e.date), float(e.amount)) for e in expenses], 
                         columns=['date', 'amount'])
        
        # Extract year-month for grouping
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
    """Generate category-wise pie chart"""
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