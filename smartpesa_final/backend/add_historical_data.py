import random
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.transaction import Transaction

def main():
    db = SessionLocal()
    business_id = 5
    start_date = datetime(2026, 2, 1)
    end_date = datetime(2026, 3, 20)

    current_date = start_date
    while current_date <= end_date:
        # Add transactions for about 85% of days
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

                transaction = Transaction(
                    business_id=business_id,
                    amount=amount,
                    type=t_type,
                    category=category,
                    description=f"Historical {t_type} for {current_date.date()}",
                    created_at=current_date
                )
                db.add(transaction)
        current_date += timedelta(days=1)

    db.commit()
    print(f"Added sample transactions from {start_date.date()} to {end_date.date()} for business {business_id}")

if __name__ == "__main__":
    main()
