from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()


class Supplier(Base):
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    country = Column(String(50))
    reliability_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)

    # Relationships
    orders = relationship("Order", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier(name='{self.name}', country='{self.country}')>"


class Inventory(Base):
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True)
    device_name = Column(String(100), nullable=False)
    device_type = Column(String(50))
    location = Column(String(50))
    quantity = Column(Integer, default=0)
    min_threshold = Column(Integer, default=10)
    price_per_unit = Column(Float)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String)
    employee_assets = relationship("EmployeeAsset", back_populates="inventory_item")


    def __repr__(self):
        return f"<Inventory(device='{self.device_name}', quantity={self.quantity})>"


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    order_date = Column(DateTime, default=datetime.datetime.utcnow)
    expected_delivery = Column(DateTime)
    status = Column(String(20), default='pending')  # pending, delivered, cancelled
    total_cost = Column(Float)

    # Relationships
    supplier = relationship("Supplier", back_populates="orders")
    deliveries = relationship("Delivery", back_populates="order")
    items = relationship("OrderItem", back_populates="order")

    def __repr__(self):
        return f"<Order(id={self.id}, status='{self.status}')>"


class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    device_name = Column(String(100))
    quantity = Column(Integer)
    unit_price = Column(Float)

    # Relationships
    order = relationship("Order", back_populates="items")


class Delivery(Base):
    __tablename__ = 'deliveries'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    delivery_date = Column(DateTime, default=datetime.datetime.utcnow)
    quality_rating = Column(Integer)  # 1-5 rating
    notes = Column(String(200))

    # Relationships
    order = relationship("Order", back_populates="deliveries")

    def __repr__(self):
        return f"<Delivery(order_id={self.order_id}, date='{self.delivery_date}')>"


# Create database engine and tables
def init_db(db_url=None):
    """Initialize the database."""
    from sqlalchemy import create_engine
    import os

    if db_url is None:
        db_url = 'sqlite:///data/db/supply_chain.sqlite'

    if db_url.startswith('sqlite:///'):
        db_path = db_url[10:]
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    engine = create_engine(db_url, echo=False)

    Base.metadata.create_all(engine)

    return engine

class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    department = Column(String(50))
    position = Column(String(50))
    join_date = Column(DateTime, default=datetime.datetime.utcnow)

    assets = relationship("EmployeeAsset", back_populates="employee")

    def __repr__(self):
        return f"<Employee(name='{self.name}', department='{self.department}')>"


class EmployeeAsset(Base):
    __tablename__ = 'employee_assets'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    inventory_id = Column(Integer, ForeignKey('inventory.id'))
    assignment_date = Column(DateTime, default=datetime.datetime.utcnow)
    expected_return_date = Column(DateTime, nullable=True)
    actual_return_date = Column(DateTime, nullable=True)
    status = Column(String(20), default='active')
    notes = Column(String(200))

    inventory_item = relationship("Inventory", back_populates="employee_assets")
    employee = relationship("Employee", back_populates="assets")
    def __repr__(self):
        return f"<EmployeeAsset(employee_id={self.employee_id}, inventory_id={self.inventory_id}, status='{self.status}')>"


