from app.database import SessionLocal
from app.models import Business, Inventory

db = SessionLocal()
try:
    # Get business
    business = db.query(Business).first()
    if not business:
        print("No business found.")
        exit()
    
    print(f"📦 Creating sample inventory for business: {business.name}")
    
    sample_items = [
        {"name": "Laptop", "sku": "LAP001", "quantity": 15, "unit": "pieces", "price_per_unit": 75000, "reorder_level": 5},
        {"name": "Printer", "sku": "PRN001", "quantity": 8, "unit": "pieces", "price_per_unit": 25000, "reorder_level": 3},
        {"name": "Paper A4", "sku": "PAP001", "quantity": 50, "unit": "reams", "price_per_unit": 500, "reorder_level": 10},
        {"name": "Desk Chair", "sku": "CHR001", "quantity": 12, "unit": "pieces", "price_per_unit": 8500, "reorder_level": 4},
        {"name": "USB Cable", "sku": "USB001", "quantity": 30, "unit": "pieces", "price_per_unit": 350, "reorder_level": 15},
        {"name": "Mouse", "sku": "MOU001", "quantity": 25, "unit": "pieces", "price_per_unit": 800, "reorder_level": 10},
        {"name": "Keyboard", "sku": "KEY001", "quantity": 20, "unit": "pieces", "price_per_unit": 1200, "reorder_level": 8},
        {"name": "Monitor", "sku": "MON001", "quantity": 10, "unit": "pieces", "price_per_unit": 18000, "reorder_level": 3},
        {"name": "External HDD", "sku": "HDD001", "quantity": 12, "unit": "pieces", "price_per_unit": 6500, "reorder_level": 4},
        {"name": "Webcam", "sku": "CAM001", "quantity": 8, "unit": "pieces", "price_per_unit": 4500, "reorder_level": 3},
    ]
    
    for item in sample_items:
        inventory = Inventory(
            name=item["name"],
            sku=item["sku"],
            quantity=item["quantity"],
            unit=item["unit"],
            price_per_unit=item["price_per_unit"],
            reorder_level=item["reorder_level"],
            business_id=business.id
        )
        db.add(inventory)
        print(f"   Added: {item['name']} - {item['quantity']} {item['unit']}")
    
    db.commit()
    print(f"\n✅ Successfully added {len(sample_items)} inventory items!")
    
finally:
    db.close()
