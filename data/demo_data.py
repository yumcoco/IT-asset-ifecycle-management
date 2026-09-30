import sys
import os
import random
import datetime
from faker import Faker
from sqlalchemy.orm import sessionmaker

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

db_dir = os.path.join(project_root, 'data', 'db')
if not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

from app.models import Supplier, Inventory, Order, OrderItem, Delivery, Employee, EmployeeAsset, init_db

db_path = os.path.join(db_dir, 'supply_chain.sqlite')
db_url = f'sqlite:///{db_path}'

engine = init_db(db_url)
Session = sessionmaker(bind=engine)
session = Session()

fake = Faker()

def generate_demo_data():
    """Generate sample data for interview demonstration"""
    print("Generating demonstration data...")

    # Clean existing data
    session.query(EmployeeAsset).delete()
    session.query(Employee).delete()
    session.query(Delivery).delete()
    session.query(OrderItem).delete()
    session.query(Order).delete()
    session.query(Inventory).delete()
    session.query(Supplier).delete()
    session.commit()

    # 1. Create suppliers
    suppliers = [
        Supplier(name="Dell Technologies", country="USA", reliability_score=4.7, quality_score=4.6),
        Supplier(name="Apple Inc.", country="USA", reliability_score=4.8, quality_score=4.9),
        Supplier(name="Lenovo", country="China", reliability_score=4.3, quality_score=4.2),
        Supplier(name="HP Inc.", country="USA", reliability_score=4.5, quality_score=4.4),
        Supplier(name="Samsung Electronics", country="South Korea", reliability_score=4.6, quality_score=4.7),
        Supplier(name="ASUS", country="Taiwan", reliability_score=4.2, quality_score=4.3),
        Supplier(name="Logitech", country="Switzerland", reliability_score=4.4, quality_score=4.5),
        Supplier(name="Microsoft", country="USA", reliability_score=4.5, quality_score=4.6)
    ]
    session.add_all(suppliers)
    session.commit()
    print(f"Created {len(suppliers)} suppliers")

    # 2. Create device inventory - Total 32 devices (30 assigned + 2 inventory)
    laptops = [
        "Dell XPS 13", "Dell Latitude 7420", "MacBook Pro 14\"", "MacBook Air M2",
        "Lenovo ThinkPad X1 Carbon", "Lenovo Yoga 9i", "HP EliteBook 840", "HP Spectre x360",
        "ASUS ZenBook Pro", "Microsoft Surface Laptop 4"
    ]

    phones = [
        "iPhone 13 Pro", "iPhone 14", "Samsung Galaxy S22", "Samsung Galaxy Note 20",
        "Google Pixel 6 Pro"
    ]

    monitors = [
        "Dell UltraSharp 27\"", "Dell P2419H 24\"", "HP Z27 27\"",
        "Samsung Odyssey G7 32\"", "ASUS ProArt PA278CV 27\""
    ]

    peripherals = [
        "Logitech MX Master 3", "Logitech MX Keys", "Logitech Brio Webcam",
        "Microsoft Ergonomic Keyboard", "Microsoft Surface Precision Mouse",
        "Dell Premier Wireless Keyboard and Mouse", "Samsung T7 SSD",
        "HP Laser Printer", "Lenovo Docking Station", "Apple AirPods Pro"
    ]

    # Add two additional devices to make total of 32
    additional_devices = [
        ("Dell XPS 15", "Laptop"),
        ("HP ProBook 450", "Laptop")
    ]

    inventory_items = []

    # Add laptops - 10 items
    for laptop in laptops:
        brand = laptop.split(" ")[0]
        supplier_id = next((s.id for s in suppliers if s.name.startswith(brand)), random.choice(suppliers).id)

        inventory = Inventory(
            device_name=laptop,
            device_type="Laptop",
            location="Headquarters",
            quantity=1,  # Each device is unique
            min_threshold=3,
            price_per_unit=random.randint(1000, 2500),
            last_updated=fake.date_time_between(start_date='-6M', end_date='now'),
            status = 'available'
        )
        inventory_items.append(inventory)

    # Add phones - 5 items
    for phone in phones:
        brand = phone.split(" ")[0]
        supplier_id = next((s.id for s in suppliers if s.name.startswith(brand)), random.choice(suppliers).id)

        inventory = Inventory(
            device_name=phone,
            device_type="Phone",
            location="Headquarters",
            quantity=1,  # Each device is unique
            min_threshold=2,
            price_per_unit=random.randint(600, 1200),
            last_updated=fake.date_time_between(start_date='-6M', end_date='now'),
            status = 'available'
        )
        inventory_items.append(inventory)

    # Add monitors - 5 items
    for monitor in monitors:
        brand = monitor.split(" ")[0]
        supplier_id = next((s.id for s in suppliers if s.name.startswith(brand)), random.choice(suppliers).id)

        inventory = Inventory(
            device_name=monitor,
            device_type="Monitor",
            location="Headquarters",
            quantity=1,  # Each device is unique
            min_threshold=2,
            price_per_unit=random.randint(300, 900),
            last_updated=fake.date_time_between(start_date='-6M', end_date='now'),
            status='available'
        )
        inventory_items.append(inventory)

    # Add peripherals - 10 items
    for peripheral in peripherals:
        brand = peripheral.split(" ")[0]
        supplier_id = next((s.id for s in suppliers if s.name.startswith(brand)), random.choice(suppliers).id)

        inventory = Inventory(
            device_name=peripheral,
            device_type="Peripheral",
            location="Headquarters",
            quantity=1,  # Each device is unique
            min_threshold=5,
            price_per_unit=random.randint(50, 200),
            last_updated=fake.date_time_between(start_date='-6M', end_date='now'),
            status='available'
        )
        inventory_items.append(inventory)

    # Add additional devices (2 items) - these will be unassigned inventory
    for device_name, device_type in additional_devices:
        brand = device_name.split(" ")[0]
        supplier_id = next((s.id for s in suppliers if s.name.startswith(brand)), random.choice(suppliers).id)

        inventory = Inventory(
            device_name=device_name,
            device_type=device_type,
            location="Headquarters",
            quantity=1,  # Each device is unique
            min_threshold=2,
            price_per_unit=random.randint(1000, 2500),
            last_updated=fake.date_time_between(start_date='-6M', end_date='now'),
            status='available'
        )
        inventory_items.append(inventory)

    session.add_all(inventory_items)
    session.commit()
    print(f"Created {len(inventory_items)} inventory items")

    # 3. Create orders to match exact device count (32)
    orders = []

    # Create 6 open orders
    print("Creating 6 open orders...")
    for i in range(1, 7):
        supplier = random.choice(suppliers)
        order_date = fake.date_time_between(start_date='-1M', end_date='-1d')

        order = Order(
            supplier_id=supplier.id,
            order_date=order_date,
            expected_delivery=order_date + datetime.timedelta(days=random.randint(7, 30)),
            status='open',
            total_cost=0  # Will be updated
        )
        session.add(order)
        session.flush()

        # Add items to the order
        total_cost = 0
        for _ in range(random.randint(1, 3)):
            inventory_item = random.choice(inventory_items)
            quantity = random.randint(1, 2)
            unit_price = inventory_item.price_per_unit

            item = OrderItem(
                order_id=order.id,
                device_name=inventory_item.device_name,
                quantity=quantity,
                unit_price=unit_price
            )
            total_cost += quantity * unit_price
            session.add(item)

        order.total_cost = total_cost
        orders.append(order)

    # Create 3 pending approval orders
    print("Creating 3 pending approval orders...")
    for i in range(1, 4):
        supplier = random.choice(suppliers)
        order_date = fake.date_time_between(start_date='-2M', end_date='-1M')

        order = Order(
            supplier_id=supplier.id,
            order_date=order_date,
            expected_delivery=order_date + datetime.timedelta(days=random.randint(7, 30)),
            status='pending',
            total_cost=0  # Will be updated
        )
        session.add(order)
        session.flush()

        # Add items to the order
        total_cost = 0
        for _ in range(random.randint(1, 3)):
            inventory_item = random.choice(inventory_items)
            quantity = random.randint(1, 2)
            unit_price = inventory_item.price_per_unit

            item = OrderItem(
                order_id=order.id,
                device_name=inventory_item.device_name,
                quantity=quantity,
                unit_price=unit_price
            )
            total_cost += quantity * unit_price
            session.add(item)

        order.total_cost = total_cost
        orders.append(order)

    # Create 5 in-transit orders
    print("Creating 5 in-transit orders...")
    for i in range(1, 6):
        supplier = random.choice(suppliers)
        order_date = fake.date_time_between(start_date='-3M', end_date='-2M')

        order = Order(
            supplier_id=supplier.id,
            order_date=order_date,
            expected_delivery=order_date + datetime.timedelta(days=random.randint(14, 45)),
            status='in-transit',
            total_cost=0  # Will be updated
        )
        session.add(order)
        session.flush()

        # Add items to the order
        total_cost = 0
        for _ in range(random.randint(1, 3)):
            inventory_item = random.choice(inventory_items)
            quantity = random.randint(1, 2)
            unit_price = inventory_item.price_per_unit

            item = OrderItem(
                order_id=order.id,
                device_name=inventory_item.device_name,
                quantity=quantity,
                unit_price=unit_price
            )
            total_cost += quantity * unit_price
            session.add(item)

        order.total_cost = total_cost
        orders.append(order)

    # Create exactly 10 delivered orders with total items matching our inventory (32)
    print("Creating delivered orders totaling 32 devices...")

    #
    order_quantities = [3, 3, 3, 3, 3, 3, 3, 3, 4, 4]  # 总和为32

    for i in range(10):
        supplier = random.choice(suppliers)
        order_date = fake.date_time_between(start_date='-6M', end_date='-3M')
        expected_delivery = order_date + datetime.timedelta(days=random.randint(7, 30))

        order = Order(
            supplier_id=supplier.id,
            order_date=order_date,
            expected_delivery=expected_delivery,
            status='delivered',
            total_cost=0  # Will be updated
        )
        session.add(order)
        session.flush()

        # 为此订单分配设备
        quantity_for_this_order = order_quantities[i]
        total_cost = 0

        # 记录添加到此订单的设备
        for j in range(quantity_for_this_order):
            # 选择一个设备 - 按照顺序选择，确保所有32个设备都被包含
            device_index = (i * 3 + j) % len(inventory_items)
            inventory_item = inventory_items[device_index]

            unit_price = inventory_item.price_per_unit

            item = OrderItem(
                order_id=order.id,
                device_name=inventory_item.device_name,
                quantity=1,
                unit_price=unit_price
            )
            total_cost += unit_price
            session.add(item)

        order.total_cost = total_cost

        # Create delivery record for completed orders
        delivery_date = order_date + datetime.timedelta(
            days=random.randint(5, (expected_delivery - order_date).days + 5))
        delivery = Delivery(
            order_id=order.id,
            delivery_date=delivery_date,
            quality_rating=random.randint(3, 5),
            notes=fake.sentence() if random.random() < 0.3 else ""
        )
        session.add(delivery)

        orders.append(order)

    session.commit()
    print(f"Created {len(orders)} orders")

    # 4. Create employees from 5 departments
    # Use exactly 5 departments
    departments = ["Engineering", "Marketing", "Finance", "IT", "Operations"]
    positions = ["Manager", "Senior", "Junior", "Intern", "Director"]

    employees = []
    # Ensure balanced distribution across departments
    for department in departments:
        # Create 4 employees per department (total 20)
        for i in range(4):
            position = positions[i] if i < len(positions) else random.choice(positions)
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
    print(f"Created {len(employees)} employees across {len(departments)} departments")

    # 5. Create employee asset assignments with consistent quantities
    # Define exact numbers for each status to maintain consistency
    active_count = 20  # 20 active assignments
    pending_return_count = 5  # 5 pending returns
    returned_count = 3  # 3 returned devices
    lost_count = 1  # 1 lost device
    damaged_count = 1  # 1 damaged device

    # 确保分配的设备是前30个设备
    assignable_inventory = inventory_items[:-2]  # 排除最后2个作为未分配的库存

    # Track assigned inventory items to prevent duplicates
    assigned_inventory_ids = set()

    asset_assignments = []

    # Create active assignments
    print(f"Creating {active_count} active assignments...")
    for i in range(active_count):
        employee = random.choice(employees)

        # 选择一个未分配的设备
        available_items = [item for item in assignable_inventory if item.id not in assigned_inventory_ids]
        inventory_item = available_items[i % len(available_items)]  # 有序选择，确保不重复
        assigned_inventory_ids.add(inventory_item.id)

        # Create active assignment
        asset = EmployeeAsset(
            employee_id=employee.id,
            inventory_id=inventory_item.id,
            assignment_date=fake.date_time_between(start_date='-1y', end_date='-1m'),
            status='active',
            notes=f"Active device assigned to {employee.name}"
        )

        # Reduce inventory quantity
        inventory_item.quantity = 0  # Mark as assigned
        inventory_item.status = 'assigned'
        asset_assignments.append(asset)

    # Create pending return assignments
    print(f"Creating {pending_return_count} pending return assignments...")
    for i in range(pending_return_count):
        employee = random.choice(employees)

        # 选择一个未分配的设备
        available_items = [item for item in assignable_inventory if item.id not in assigned_inventory_ids]
        inventory_item = available_items[i % len(available_items)]  # 有序选择，确保不重复
        assigned_inventory_ids.add(inventory_item.id)

        # Assignment dates
        assignment_date = fake.date_time_between(start_date='-1y', end_date='-3m')
        expected_return_date = assignment_date + datetime.timedelta(days=random.randint(90, 180))

        # Create pending return assignment
        asset = EmployeeAsset(
            employee_id=employee.id,
            inventory_id=inventory_item.id,
            assignment_date=assignment_date,
            expected_return_date=expected_return_date,
            status='pending_return',
            notes=f"Device scheduled for return by {expected_return_date.strftime('%Y-%m-%d')}"
        )

        # Reduce inventory quantity
        inventory_item.quantity = 0  # Mark as assigned
        inventory_item.status = 'assigned'
        asset_assignments.append(asset)

    # Create returned assignments
    print(f"Creating {returned_count} returned assignments...")
    for i in range(returned_count):
        employee = random.choice(employees)

        #
        available_items = [item for item in assignable_inventory if item.id not in assigned_inventory_ids]
        inventory_item = available_items[i % len(available_items)]  #
        assigned_inventory_ids.add(inventory_item.id)

        # Assignment dates
        assignment_date = fake.date_time_between(start_date='-1y', end_date='-6m')
        expected_return_date = assignment_date + datetime.timedelta(days=random.randint(90, 180))
        actual_return_date = expected_return_date + datetime.timedelta(days=random.randint(-10, 10))

        # Create returned assignment
        asset = EmployeeAsset(
            employee_id=employee.id,
            inventory_id=inventory_item.id,
            assignment_date=assignment_date,
            expected_return_date=expected_return_date,
            actual_return_date=actual_return_date,
            status='returned',
            notes=f"Device returned on {actual_return_date.strftime('%Y-%m-%d')}"
        )

        # Device is available again since it was returned - BUT quantity stays 0 because we want it in the assigned pool
        inventory_item.quantity = 1  # "returned"

        # "returned"
        inventory_item.status = 'returned'
        inventory_item.status = 'available'
        asset_assignments.append(asset)

    # Create lost assignments
    print(f"Creating {lost_count} lost assignments...")
    for i in range(lost_count):
        employee = random.choice(employees)

        available_items = [item for item in assignable_inventory if item.id not in assigned_inventory_ids]
        inventory_item = available_items[i % len(available_items)]
        assigned_inventory_ids.add(inventory_item.id)

        # Assignment dates
        assignment_date = fake.date_time_between(start_date='-1y', end_date='-3m')
        expected_return_date = assignment_date + datetime.timedelta(days=random.randint(90, 180))

        # Create lost assignment
        asset = EmployeeAsset(
            employee_id=employee.id,
            inventory_id=inventory_item.id,
            assignment_date=assignment_date,
            expected_return_date=expected_return_date,
            status='lost',
            notes="Device reported as lost"
        )

        # Lost device is not available
        inventory_item.quantity = 0
        inventory_item.status = 'assigned'
        asset_assignments.append(asset)

    # Create damaged assignments
    print(f"Creating {damaged_count} damaged assignments...")
    for i in range(damaged_count):
        employee = random.choice(employees)

        available_items = [item for item in assignable_inventory if item.id not in assigned_inventory_ids]
        inventory_item = available_items[i % len(available_items)]  # 有序选择，确保不重复
        assigned_inventory_ids.add(inventory_item.id)

        # Assignment dates
        assignment_date = fake.date_time_between(start_date='-1y', end_date='-3m')
        expected_return_date = assignment_date + datetime.timedelta(days=random.randint(90, 180))
        actual_return_date = expected_return_date + datetime.timedelta(days=random.randint(-10, 10))

        # Create damaged assignment
        asset = EmployeeAsset(
            employee_id=employee.id,
            inventory_id=inventory_item.id,
            assignment_date=assignment_date,
            expected_return_date=expected_return_date,
            actual_return_date=actual_return_date,
            status='damaged',
            notes="Device returned with significant damage"
        )

        # Damaged device is not available
        inventory_item.quantity = 0
        inventory_item.status = 'assigned'
        asset_assignments.append(asset)

    session.add_all(asset_assignments)

    # 确保最后两个设备是可用的库存 (quantity=1)
    for item in inventory_items[-2:]:
        item.quantity = 1
        item.status = 'available'

    session.commit()

    # Verify the counts for each status
    active_actual = session.query(EmployeeAsset).filter(EmployeeAsset.status == 'active').count()
    pending_actual = session.query(EmployeeAsset).filter(EmployeeAsset.status == 'pending_return').count()
    returned_actual = session.query(EmployeeAsset).filter(EmployeeAsset.status == 'returned').count()
    lost_actual = session.query(EmployeeAsset).filter(EmployeeAsset.status == 'lost').count()
    damaged_actual = session.query(EmployeeAsset).filter(EmployeeAsset.status == 'damaged').count()

    # Calculate available devices (those with quantity > 0, should be just the last 2)
    available_actual = session.query(Inventory).filter(Inventory.quantity > 0).count()

    assigned_actual = session.query(Inventory).filter(Inventory.quantity == 0).count()

    print(f"Created {len(asset_assignments)} employee asset assignments with following status distribution:")
    print(f"- Active: {active_actual}")
    print(f"- Pending Return: {pending_actual}")
    print(f"- Returned: {returned_actual}")
    print(f"- Lost: {lost_actual}")
    print(f"- Damaged: {damaged_actual}")
    print(f"- Available devices (unassigned inventory): {available_actual}")
    print(f"- Assigned devices (all statuses): {assigned_actual}")
    print(f"- Total devices: {len(inventory_items)}")

    # Calculate total asset value
    total_value = session.query(Inventory).with_entities(
        Inventory.price_per_unit
    ).all()
    total_value_sum = sum([price for (price,) in total_value])
    print(f"Total asset value: ${total_value_sum:,.2f}")

    print("Demo data generation complete!")


if __name__ == "__main__":
    generate_demo_data()