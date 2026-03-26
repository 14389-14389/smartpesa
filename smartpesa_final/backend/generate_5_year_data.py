import random
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.transaction import Transaction

def generate_5_year_data():
    db = SessionLocal()
    business_id = 5

    # Clear existing transactions for this business
    db.query(Transaction).filter(Transaction.business_id == business_id).delete()
    print("Cleared existing transactions for business", business_id)

    # Date range: 5 years back from today
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=5*365)
    print(f"Generating data from {start_date} to {end_date}")

    count = 0
    current = start_date

    while current <= end_date:
        # Day of week and month
        dow = current.weekday()
        is_weekend = dow >= 5
        month = current.month

        # Base sales (KES 10,000 average)
        base_sales = 10000

        # Weekend increase
        if is_weekend:
            base_sales *= 1.3

        # Seasonal factor (higher in Dec, lower in Jan-Mar)
        if month == 12:
            base_sales *= 1.4
        elif month in [1, 2, 3]:
            base_sales *= 0.9

        # Random noise
        noise = random.uniform(0.7, 1.3)
        sales_amount = round(base_sales * noise, 2)

        # Add sales on 98% of days
        if random.random() < 0.98:
            trans = Transaction(
                business_id=business_id,
                amount=sales_amount,
                type='income',
                category='Sales',
                description=f"Daily sales on {current}",
                created_at=datetime.combine(current, datetime.min.time())
            )
            db.add(trans)
            count += 1

        # Add monthly expenses on the 1st of each month
        if current.day == 1:
            rent = random.uniform(8000, 12000)
            salaries = random.uniform(15000, 25000)
            for amount, cat in [(rent, 'Rent'), (salaries, 'Salaries')]:
                expense = Transaction(
                    business_id=business_id,
                    amount=amount,
                    type='expense',
                    category=cat,
                    description=f"{cat} for {current.strftime('%B %Y')}",
                    created_at=datetime.combine(current, datetime.min.time())
                )
                db.add(expense)
                count += 1

        # Add occasional small expenses (20% of days)
        if random.random() < 0.2:
            other_amount = random.uniform(200, 1500)
            cat = random.choice(['Utilities', 'Marketing', 'Supplies'])
            expense = Transaction(
                business_id=business_id,
                amount=other_amount,
                type='expense',
                category=cat,
                description=f"{cat} expense on {current}",
                created_at=datetime.combine(current, datetime.min.time())
            )
            db.add(expense)
            count += 1

        current += timedelta(days=1)

        # Commit every 500 records to keep memory low
        if count % 500 == 0:
            db.commit()
            print(f"Committed at {count} transactions")

    db.commit()
    db.close()
    print(f"Generated {count} transactions for business {business_id}")

if __name__ == "__main__":
    generate_5_year_data()
