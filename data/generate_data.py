import sys
import os
import random
import datetime
from faker import Faker
from sqlalchemy.orm import sessionmaker
import pandas as pd

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import Supplier, Inventory, Order, OrderItem, Delivery, init_db, EmployeeAsset, Employee

fake = Faker()

# Initialize database
engine = init_db()
Session = sessionmaker(bind=engine)
session = Session()


def generate_suppliers(count=8):
    """Generate mock supplier data"""
    countries = ['USA', 'China', 'Japan', 'Germany', 'India', 'UK', 'Taiwan', 'South Korea']
    suppliers = []

    for i in range(count):
        supplier = Supplier(
            name=fake.company(),
            country=countries[i % len(countries)],
            reliability_score=round(random.uniform(3.0, 5.0), 1),
            quality_score=round(random.uniform(3.0, 5.0), 1)
        )
        suppliers.append(supplier)

    session.add_all(suppliers)
    session.commit()
    return suppliers


def generate_inventory(count=200):
    """Generate mock inventory data"""
    device_types = ['Laptop', 'Desktop', 'Server', 'Tablet', 'Phone', 'Printer', 'Network Switch', 'Router']
    locations = ['USA', 'China', 'Japan', 'Germany', 'India', 'UK', 'Canada', 'France', 'Brazil', 'Australia']
    inventory_items = []

    for i in range(count):
        inventory = Inventory(
            device_name=f"{fake.company()} {random.choice(['Pro', 'Elite', 'Standard', 'Ultimate'])} {fake.word().capitalize()}",
            device_type=random.choice(device_types),
            location=random.choice(locations),
            quantity=random.randint(0, 100),
            min_threshold=random.randint(5, 15),
            price_per_unit=round(random.uniform(100, 5000), 2),
            last_updated=fake.date_time_between(start_date='-6M', end_date='now')
        )
        inventory_items.append(inventory)

    session.add_all(inventory_items)
    session.commit()
    return inventory_items


def generate_orders_and_deliveries(suppliers, inventory_items, order_count=150):
    """Generate mock order and delivery data"""

    for _ in range(order_count):
        # Create an order
        supplier = random.choice(suppliers)
        order_date = fake.date_time_between(start_date='-6M', end_date='now')

        # Expected delivery between 3 and 20 days after order
        expected_delivery = order_date + datetime.timedelta(days=random.randint(3, 20))

        # Determine status based on dates
        today = datetime.datetime.now()
        if expected_delivery > today:
            status = 'pending'
        else:
            status = random.choices(['delivered', 'cancelled'], weights=[0.9, 0.1])[0]

        # Create the order
        order = Order(
            supplier_id=supplier.id,
            order_date=order_date,
            expected_delivery=expected_delivery,
            status=status,
            total_cost=0  # Will calculate based on items
        )
        session.add(order)
        session.flush()  # To get the order ID

        # Add 1-5 items to the order
        total_cost = 0
        for _ in range(random.randint(1, 5)):
            item = random.choice(inventory_items)
            quantity = random.randint(1, 20)
            unit_price = item.price_per_unit

            order_item = OrderItem(
                order_id=order.id,
                device_name=item.device_name,
                quantity=quantity,
                unit_price=unit_price
            )

            total_cost += quantity * unit_price
            session.add(order_item)

        # Update the total cost
        order.total_cost = round(total_cost, 2)

        # If delivered, create a delivery record
        if status == 'delivered':
            # Delivery date between order date and expected delivery (or slightly late)
            on_time = random.choices([True, False], weights=[0.8, 0.2])[0]

            if on_time:
                delivery_date = order_date + datetime.timedelta(
                    days=random.randint(1, (expected_delivery - order_date).days))
            else:
                delivery_date = expected_delivery + datetime.timedelta(days=random.randint(1, 10))

            delivery = Delivery(
                order_id=order.id,
                delivery_date=delivery_date,
                quality_rating=random.randint(1, 5),
                notes=fake.sentence() if random.random() < 0.3 else ""
            )
            session.add(delivery)

    session.commit()


def export_to_csv():
    """Export database data to CSV files for ETL processing"""
    # Create directory if it doesn't exist
    os.makedirs('data/csv', exist_ok=True)

    # Export suppliers
    suppliers = session.query(Supplier).all()
    suppliers_df = pd.DataFrame([{
        'id': s.id,
        'name': s.name,
        'country': s.country,
        'reliability_score': s.reliability_score,
        'quality_score': s.quality_score
    } for s in suppliers])
    suppliers_df.to_csv('data/csv/suppliers.csv', index=False)

    # Export inventory
    inventory = session.query(Inventory).all()
    inventory_df = pd.DataFrame([{
        'id': i.id,
        'device_name': i.device_name,
        'device_type': i.device_type,
        'location': i.location,
        'quantity': i.quantity,
        'min_threshold': i.min_threshold,
        'price_per_unit': i.price_per_unit,
        'last_updated': i.last_updated
    } for i in inventory])
    inventory_df.to_csv('data/csv/inventory.csv', index=False)

    # Export orders
    orders = session.query(Order).all()
    orders_df = pd.DataFrame([{
        'id': o.id,
        'supplier_id': o.supplier_id,
        'order_date': o.order_date,
        'expected_delivery': o.expected_delivery,
        'status': o.status,
        'total_cost': o.total_cost
    } for o in orders])
    orders_df.to_csv('data/csv/orders.csv', index=False)

    # Export deliveries
    deliveries = session.query(Delivery).all()
    deliveries_df = pd.DataFrame([{
        'id': d.id,
        'order_id': d.order_id,
        'delivery_date': d.delivery_date,
        'quality_rating': d.quality_rating,
        'notes': d.notes
    } for d in deliveries])
    deliveries_df.to_csv('data/csv/deliveries.csv', index=False)

    print("Data exported to CSV files in data/csv directory")

def generate_employees(count=50):
    """Generate mock employee data"""
    departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'IT', 'Operations', 'Customer Support']
    positions = ['Manager', 'Senior', 'Junior', 'Intern', 'Lead', 'Director']
    employees = []

    for i in range(count):
        department = random.choice(departments)
        position = random.choice(positions)

        employee = Employee(
            name=fake.name(),
            email=fake.email(),
            department=department,
            position=f"{position} {department.rstrip('s')}",
            join_date=fake.date_time_between(start_date='-3y', end_date='now')
        )
        employees.append(employee)

    session.add_all(employees)
    session.commit()
    return employees


def generate_employee_assets(employees, inventory_items, count=100):
    """Generate mock employee asset assignments"""
    statuses = ['active', 'active', 'active', 'pending_return', 'returned', 'lost', 'damaged']
    assignments = []

    assigned_inventory_ids = set()

    for _ in range(count):
        employee = random.choice(employees)

        available_items = [item for item in inventory_items if item.id not in assigned_inventory_ids]

        if not available_items:
            break

        inventory_item = random.choice(available_items)
        status = random.choice(statuses)

        assignment_date = fake.date_time_between(start_date='-1y', end_date='now')
        expected_return_date = None
        actual_return_date = None

        if status in ['pending_return', 'returned', 'lost', 'damaged']:
            expected_return_date = assignment_date + datetime.timedelta(days=random.randint(90, 365))

            if status in ['returned', 'lost', 'damaged']:
                max_return_date = min(expected_return_date + datetime.timedelta(days=30), datetime.datetime.now())
                actual_return_date = fake.date_time_between(start_date=expected_return_date,
                                                            end_date=max_return_date)

        asset = EmployeeAsset(
            employee_id=employee.id,
            inventory_id=inventory_item.id,
            assignment_date=assignment_date,
            expected_return_date=expected_return_date,
            actual_return_date=actual_return_date,
            status=status,
            notes=fake.sentence() if random.random() < 0.3 else ""
        )

        assignments.append(asset)

        if status == 'active':
            assigned_inventory_ids.add(inventory_item.id)

    session.add_all(assignments)
    session.commit()
    return assignments



if __name__ == "__main__":
    # Clean existing data
    session.query(Delivery).delete()
    session.query(OrderItem).delete()
    session.query(Order).delete()
    session.query(Inventory).delete()
    session.query(Supplier).delete()
    session.commit()

    print("Generating suppliers...")
    suppliers = generate_suppliers()

    print("Generating inventory...")
    inventory = generate_inventory()

    print("Generating orders and deliveries...")
    generate_orders_and_deliveries(suppliers, inventory)

    print("Exporting data to CSV...")
    export_to_csv()

    print("Data generation complete!")
    session.query(EmployeeAsset).delete()
    session.query(Employee).delete()
    session.query(Delivery).delete()
    session.query(OrderItem).delete()
    session.query(Order).delete()
    session.query(Inventory).delete()
    session.query(Supplier).delete()
    session.commit()

    print("Generating suppliers...")
    suppliers = generate_suppliers()

    print("Generating inventory...")
    inventory = generate_inventory()

    print("Generating orders and deliveries...")
    generate_orders_and_deliveries(suppliers, inventory)

    print("Generating employees...")
    employees = generate_employees()

    print("Generating employee asset assignments...")
    generate_employee_assets(employees, inventory)

    print("Exporting data to CSV...")
    export_to_csv()

    print("Data generation complete!")


