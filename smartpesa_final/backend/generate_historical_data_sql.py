import random
from datetime import datetime, timedelta
from app.database import engine
from sqlalchemy import text

def main():
    business_id = 1
    start_date = datetime(2026, 2, 1)
    end_date = datetime(2026, 3, 20)

    with engine.connect() as conn:
        current_date = start_date
        while current_date <= end_date:
            # Add transactions for most days (85% of days)
            if random.random() < 0.85:
                num_transactions = random.randint(1, 6)
                for _ in range(num_transactions):
                    # 65% income, 35% expense
                    if random.random() < 0.65:
                        t_type = 'income'
                        amount = random.uniform(2000, 80000)
                        category = random.choice(['Sales', 'Services', 'Consulting', 'Product Sales'])
                    else:
                        t_type = 'expense'
                        amount = random.uniform(500, 25000)
                        category = random.choice(['Rent', 'Utilities', 'Salaries', 'Marketing', 'Supplies'])
                    
                    # Insert directly using raw SQL
                    conn.execute(
                        text("""
                            INSERT INTO transactions (business_id, amount, type, category, description, created_at)
                            VALUES (:business_id, :amount, :type, :category, :description, :created_at)
                        """),
                        {
                            'business_id': business_id,
                            'amount': amount,
                            'type': t_type,
                            'category': category,
                            'description': f"Historical {t_type} for {current_date.date()}",
                            'created_at': current_date
                        }
                    )
            current_date += timedelta(days=1)
        conn.commit()
    print(f"Added sample transactions from {start_date.date()} to {end_date.date()}")

if __name__ == "__main__":
    main()
