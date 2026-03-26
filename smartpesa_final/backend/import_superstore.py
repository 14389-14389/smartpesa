import pandas as pd
from datetime import datetime
from app.database import SessionLocal
from app.models.transaction import Transaction

CSV_FILE = "train.csv"
BUSINESS_ID = 5

def main():
    db = SessionLocal()
    df = pd.read_csv(CSV_FILE, encoding='latin-1')
    print("Columns in dataset:", df.columns.tolist())

    # Convert 'Order Date' with dayfirst=True because dates are DD/MM/YYYY
    df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True)
    daily_sales = df.groupby(df['Order Date'].dt.date)['Sales'].sum().reset_index()
    daily_sales.columns = ['date', 'amount']

    today = datetime.now().date()
    daily_sales = daily_sales[daily_sales['date'] <= today]

    count = 0
    for _, row in daily_sales.iterrows():
        trans = Transaction(
            business_id=BUSINESS_ID,
            amount=round(row['amount'], 2),
            type='income',
            category='Sales',
            description=f"Sales on {row['date']}",
            created_at=datetime.combine(row['date'], datetime.min.time())
        )
        db.add(trans)
        count += 1

    db.commit()
    db.close()
    print(f"✅ Imported {count} sales transactions for business {BUSINESS_ID}")

if __name__ == "__main__":
    main()