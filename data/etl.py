import pandas as pd
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import Supplier, Inventory, Order, Delivery, init_db, Employee, EmployeeAsset


def load_and_process_data():
    """Load data from CSVs, clean, transform, and load into SQLite database"""
    print("Starting ETL process...")

    # Initialize database connection
    engine = init_db()
    Session = sessionmaker(bind=engine)
    session = Session()

    # Load CSV files
    csv_dir = 'data/csv'
    suppliers_df = pd.read_csv(f'{csv_dir}/suppliers.csv')
    inventory_df = pd.read_csv(f'{csv_dir}/inventory.csv')
    orders_df = pd.read_csv(f'{csv_dir}/orders.csv')
    deliveries_df = pd.read_csv(f'{csv_dir}/deliveries.csv')

    # Data cleaning and transformation

    # Convert date strings to datetime objects
    for df in [inventory_df, orders_df, deliveries_df]:
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col])

    # Calculate supplier performance metrics
    calculate_supplier_metrics(suppliers_df, orders_df, deliveries_df)

    # Calculate inventory alerts
    inventory_df['status'] = inventory_df.apply(
        lambda row: 'Low' if row['quantity'] <= row['min_threshold'] else 'OK', axis=1)

    # Save processed data back to CSVs
    processed_dir = 'data/processed'
    os.makedirs(processed_dir, exist_ok=True)

    suppliers_df.to_csv(f'{processed_dir}/suppliers_processed.csv', index=False)
    inventory_df.to_csv(f'{processed_dir}/inventory_processed.csv', index=False)

    # Create analytics views
    create_analytics_views(suppliers_df, inventory_df, orders_df, deliveries_df)
    employees_df = process_employee_data(session)
    assignments_df = process_asset_assignments(session, employees_df)
    print("ETL process completed successfully")


def calculate_supplier_metrics(suppliers_df, orders_df, deliveries_df):
    """Calculate performance metrics for suppliers based on order and delivery data"""
    # Merge orders with deliveries
    merged_df = pd.merge(
        orders_df,
        deliveries_df,
        how='left',
        left_on='id',
        right_on='order_id'
    )

    # Calculate on-time delivery percentage
    # An order is considered on-time if delivery_date <= expected_delivery
    merged_df['on_time'] = merged_df.apply(
        lambda row: 1 if pd.notna(row['delivery_date']) and row['delivery_date'] <= row['expected_delivery'] else 0,
        axis=1
    )

    # Group by supplier and calculate metrics
    supplier_metrics = merged_df.groupby('supplier_id').agg(
        total_orders=('id', 'count'),
        delivered_orders=('delivery_date', lambda x: x.notna().sum()),
        on_time_deliveries=('on_time', 'sum'),
        avg_quality_rating=('quality_rating', 'mean')
    ).reset_index()

    # Calculate on-time delivery percentage
    supplier_metrics['on_time_pct'] = supplier_metrics.apply(
        lambda row: (row['on_time_deliveries'] / row['delivered_orders'] * 100)
        if row['delivered_orders'] > 0 else 0,
        axis=1
    )

    # Update supplier dataframe with calculated metrics
    for _, row in supplier_metrics.iterrows():
        idx = suppliers_df.index[suppliers_df['id'] == row['supplier_id']].tolist()
        if idx:
            # Update reliability score based on on-time percentage
            suppliers_df.at[idx[0], 'reliability_score'] = min(5, row['on_time_pct'] / 20)
            # Update quality score based on average quality rating
            if not pd.isna(row['avg_quality_rating']):
                suppliers_df.at[idx[0], 'quality_score'] = row['avg_quality_rating']


def create_analytics_views(suppliers_df, inventory_df, orders_df, deliveries_df):
    """Create specialized views for analytics dashboards"""
    views_dir = 'data/views'
    os.makedirs(views_dir, exist_ok=True)

    # 1. Inventory status by location
    inventory_by_location = inventory_df.groupby('location').agg(
        total_devices=('id', 'count'),
        total_quantity=('quantity', 'sum'),
        low_stock_items=('status', lambda x: (x == 'Low').sum()),
        total_value=('price_per_unit', lambda x: (x * inventory_df.loc[x.index, 'quantity']).sum())
    ).reset_index()

    inventory_by_location.to_csv(f'{views_dir}/inventory_by_location.csv', index=False)

    # 2. Supplier performance comparison
    supplier_performance = suppliers_df[['id', 'name', 'country', 'reliability_score', 'quality_score']]

    # Add total order value
    supplier_orders = orders_df.groupby('supplier_id').agg(
        total_orders=('id', 'count'),
        total_spend=('total_cost', 'sum')
    ).reset_index()

    supplier_performance = pd.merge(
        supplier_performance,
        supplier_orders,
        how='left',
        left_on='id',
        right_on='supplier_id'
    )

    supplier_performance.to_csv(f'{views_dir}/supplier_performance.csv', index=False)

    # 3. Device type analysis
    device_analysis = inventory_df.groupby('device_type').agg(
        total_count=('id', 'count'),
        avg_price=('price_per_unit', 'mean'),
        total_value=('price_per_unit', lambda x: (x * inventory_df.loc[x.index, 'quantity']).sum())
    ).reset_index()

    device_analysis.to_csv(f'{views_dir}/device_analysis.csv', index=False)

    # 4. Order timeline for last 6 months
    orders_df['month'] = orders_df['order_date'].dt.strftime('%Y-%m')
    monthly_orders = orders_df.groupby('month').agg(
        order_count=('id', 'count'),
        total_spend=('total_cost', 'sum')
    ).reset_index()

    monthly_orders.to_csv(f'{views_dir}/monthly_orders.csv', index=False)


def process_employee_data(session):
    """Process employee data for analytics"""
    print("Processing employee data...")

    # 将员工数据导出为CSV
    employees = session.query(Employee).all()
    employees_df = pd.DataFrame([{
        'id': e.id,
        'name': e.name,
        'email': e.email,
        'department': e.department,
        'position': e.position,
        'join_date': e.join_date
    } for e in employees])

    # 保存处理后的员工数据
    os.makedirs('data/processed', exist_ok=True)
    employees_df.to_csv('data/processed/employees_processed.csv', index=False)

    return employees_df


def process_asset_assignments(session, employees_df):
    """Process employee asset assignment data for analytics"""
    print("Processing asset assignments...")

    # 获取资产分配数据
    asset_query = session.query(
        EmployeeAsset, Employee, Inventory
    ).join(
        Employee, EmployeeAsset.employee_id == Employee.id
    ).join(
        Inventory, EmployeeAsset.inventory_id == Inventory.id
    ).all()

    # 转换为DataFrame
    assignments_df = pd.DataFrame([{
        'id': a.id,
        'employee_id': a.employee_id,
        'employee_name': e.name,
        'department': e.department,
        'inventory_id': a.inventory_id,
        'device_name': i.device_name,
        'device_type': i.device_type,
        'assignment_date': a.assignment_date,
        'expected_return_date': a.expected_return_date,
        'actual_return_date': a.actual_return_date,
        'status': a.status,
        'notes': a.notes
    } for a, e, i in asset_query])

    # 保存处理后的分配数据
    assignments_df.to_csv('data/processed/asset_assignments_processed.csv', index=False)

    # 创建分析视图
    create_assignment_analytics_views(assignments_df, employees_df)

    return assignments_df


def create_assignment_analytics_views(assignments_df, employees_df):
    """Create analytics views for asset assignments"""
    views_dir = 'data/views'
    os.makedirs(views_dir, exist_ok=True)

    # 1. 部门资产分配视图
    dept_assets = assignments_df[assignments_df['status'] == 'active'].groupby('department').agg(
        total_assets=('id', 'count')
    ).reset_index()

    # 添加部门总人数
    dept_employees = employees_df.groupby('department').agg(
        total_employees=('id', 'count')
    ).reset_index()

    dept_view = pd.merge(
        dept_assets,
        dept_employees,
        on='department',
        how='outer'
    ).fillna(0)

    # 计算人均设备数
    dept_view['assets_per_employee'] = dept_view['total_assets'] / dept_view['total_employees']
    dept_view.to_csv(f'{views_dir}/department_assets.csv', index=False)

    # 2. 设备状态分布
    status_view = assignments_df.groupby('status').agg(
        count=('id', 'count')
    ).reset_index()
    status_view.to_csv(f'{views_dir}/asset_status.csv', index=False)

    # 3. 设备类型分配
    device_type_view = assignments_df[assignments_df['status'] == 'active'].groupby('device_type').agg(
        count=('id', 'count')
    ).reset_index()
    device_type_view.to_csv(f'{views_dir}/device_type_distribution.csv', index=False)

    # 4. 最近分配和待返回
    recent_assignments = assignments_df.sort_values(
        by='assignment_date', ascending=False
    ).head(20)
    recent_assignments.to_csv(f'{views_dir}/recent_assignments.csv', index=False)

    pending_returns = assignments_df[
        assignments_df['status'] == 'pending_return'
        ].sort_values(by='expected_return_date')
    pending_returns.to_csv(f'{views_dir}/pending_returns.csv', index=False)


if __name__ == "__main__":
    load_and_process_data()