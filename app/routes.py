from flask import render_template
import pandas as pd
import json
import os
from sqlalchemy import func, case, or_
from datetime import datetime, timedelta
from flask import jsonify, request
from app import app, Session
from app.models import Employee, EmployeeAsset, Inventory, Supplier, Order, Delivery, OrderItem


@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')


@app.route('/employee-assets')
def employee_assets():
    """Render the employee assets page"""
    return render_template('employee-assets.html')

@app.route('/inventory')
def inventory():
    """Render the inventory page"""
    return render_template('inventory.html')

@app.route('/vendors')
def vendors():
    """Render the vendors page"""
    return render_template('vendors.html')

@app.route('/procurement')
def procurement():
    """Render the procurement page"""
    return render_template('procurement.html')


# API Endpoints

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
   """Get inventory data, simplified to just show available and assigned devices"""
   try:
       session = Session()
       query = session.query(Inventory)

       # Process filter parameters
       status = request.args.get('status')
       device_type = request.args.get('device_type')
       search = request.args.get('search')

       # Filter by status
       if status:
           if status.lower() == 'available':
               # Available devices condition: quantity > 0
               query = query.filter(Inventory.quantity > 0)
           elif status.lower() == 'assigned':
               # Assigned devices condition: quantity = 0
               query = query.filter(Inventory.quantity == 0)

       # Filter by device type
       if device_type:
           query = query.filter(Inventory.device_type == device_type)

       # Search functionality
       if search:
           search_term = f"%{search}%"
           query = query.filter(
               or_(
                   Inventory.device_name.ilike(search_term),
                   Inventory.device_type.ilike(search_term),
                   Inventory.location.ilike(search_term)
               )
           )

       # Query devices
       inventory_items = query.all()

       # Build response data
       inventory_data = []
       for item in inventory_items:
           # Simplified status logic - only distinguish between "available" and "assigned"
           is_available = item.quantity > 0
           simplified_status = 'available' if is_available else 'assigned'

           device_data = {
               'id': item.id,
               'device_name': item.device_name,
               'device_type': item.device_type,
               'location': item.location or 'Headquarters',
               'quantity': item.quantity,
               'min_threshold': item.min_threshold,
               'price_per_unit': item.price_per_unit,
               'last_updated': item.last_updated.isoformat() if item.last_updated else None,
               'status': simplified_status,
               'is_available': is_available
           }
           inventory_data.append(device_data)

       # Calculate simplified statistics
       total = len(inventory_items)
       available = sum(1 for item in inventory_items if item.quantity > 0)
       assigned = total - available

       # Build response
       response_data = {
           'data': inventory_data,
           'summary': {
               'total': total,
               'available': available,
               'assigned': assigned
           }
       }
       print(f"API response: Total devices={total}, Available={available}, Assigned={assigned}")
       return jsonify(response_data)
   except Exception as e:
       print(f"Error in get_inventory: {e}")
       import traceback
       traceback.print_exc()
       return jsonify({'error': str(e)}), 500
   finally:
       session.close()


@app.route('/api/inventory/<int:device_id>', methods=['GET'])
def get_device_detail(device_id):
    """Get detailed information for a specific device with simplified status"""
    try:
        session = Session()

        device = session.query(Inventory).filter(Inventory.id == device_id).first()

        if not device:
            return jsonify({'error': 'Device not found'}), 404

        is_available = device.quantity > 0
        simplified_status = 'available' if is_available else 'assigned'

        device_data = {
            'id': device.id,
            'device_name': device.device_name,
            'device_type': device.device_type,
            'location': device.location or 'Headquarters',
            'quantity': device.quantity,
            'min_threshold': device.min_threshold,
            'price_per_unit': device.price_per_unit,
            'last_updated': device.last_updated.isoformat() if device.last_updated else None,
            'status': simplified_status,
            'is_available': is_available,
            'notes': device.notes if hasattr(device, 'notes') else ''
        }

        return jsonify({
            'data': device_data,
            'success': True
        })
    except Exception as e:
        print(f"Error getting device details: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/inventory/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    """Update a device in inventory"""
    try:
        data = request.json
        session = Session()

        # Find the device
        device = session.query(Inventory).get(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404

        # Update device fields
        if 'device_name' in data:
            device.device_name = data['device_name']
        if 'device_type' in data:
            device.device_type = data['device_type']
        if 'location' in data:
            device.location = data['location']
        if 'price_per_unit' in data:
            device.price_per_unit = data['price_per_unit']
        if 'notes' in data and hasattr(device, 'notes'):
            device.notes = data['notes']

        # Update last_updated timestamp
        device.last_updated = datetime.now()

        session.commit()

        return jsonify({
            'success': True,
            'message': 'Device updated successfully'
        })
    except Exception as e:
        session.rollback()
        print(f"Error updating device: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/suppliers', methods=['GET'])
def get_suppliers():
    """Get supplier data"""
    try:
        session = Session()
        suppliers = session.query(Supplier).all()

        suppliers_data = []
        for supplier in suppliers:
            orders = session.query(Order).filter(Order.supplier_id == supplier.id).all()

            total_orders = len(orders)
            total_spend = sum(order.total_cost for order in orders if order.total_cost)

            supplier_data = {
                'id': supplier.id,
                'name': supplier.name,
                'country': supplier.country,
                'reliability_score': supplier.reliability_score,
                'quality_score': supplier.quality_score,
                'total_orders': total_orders,
                'total_spend': total_spend
            }
            suppliers_data.append(supplier_data)

        return jsonify({
            'data': suppliers_data,
            'count': len(suppliers_data)
        })
    except Exception as e:
        print(f"Error in get_suppliers: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get orders, optionally filtered by status"""
    status_param = request.args.get('status', None)

    status_mapping = {
        'completed': 'delivered',
        'pending': 'pending',
        'in-transit': 'in-transit',
        'all': None,
        'open': 'open'
    }

    db_status = status_mapping.get(status_param, status_param)

    try:
        session = Session()
        print(f"Fetching orders with status filter: {status_param} (maps to DB status: {db_status})")

        query = session.query(Order).join(Supplier, Order.supplier_id == Supplier.id)

        if db_status:
            query = query.filter(Order.status == db_status)

        orders = query.all()
        print(f"Found {len(orders)} orders matching status: {db_status}")

        order_ids = [order.id for order in orders]
        item_counts = {}
        if order_ids:
            item_count_results = session.query(
                OrderItem.order_id,
                func.count(OrderItem.id).label('count')
            ).filter(
                OrderItem.order_id.in_(order_ids)
            ).group_by(
                OrderItem.order_id
            ).all()

            item_counts = {order_id: count for order_id, count in item_count_results}

        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'orderNumber': f"PO-2025-{order.id:03d}",
                'vendor': order.supplier.name,
                'date': order.order_date.strftime('%Y-%m-%d') if order.order_date else None,
                'items': item_counts.get(order.id, 0),
                'total': f"${order.total_cost:,.0f}" if order.total_cost else "$0",
                'status': order.status
            })

        return jsonify({
            'data': orders_data,
            'count': len(orders_data)
        })
    except Exception as e:
        print(f"Error in get_orders: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/orders/counts', methods=['GET'])
def get_order_counts():
    """Get counts of orders by status"""
    try:
        session = Session()

        status_counts = session.query(
            Order.status,
            func.count(Order.id).label('count')
        ).group_by(
            Order.status
        ).all()

        counts = {status: count for status, count in status_counts}

        return jsonify({
            'open': counts.get('open', 0),
            'pending': counts.get('pending', 0),
            'in_transit': counts.get('in-transit', 0),
            'completed': counts.get('delivered', 0)  # 注意这里的映射
        })
    except Exception as e:
        print(f"Error in get_order_counts: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/orders/debug', methods=['GET'])
def debug_orders():
    """Debug endpoint to check all order statuses in the database"""
    try:
        session = Session()

        status_counts = session.query(
            Order.status,
            func.count(Order.id).label('count')
        ).group_by(
            Order.status
        ).all()

        sample_orders = session.query(Order).limit(10).all()
        sample_data = [{
            'id': order.id,
            'status': order.status,
            'order_date': order.order_date.isoformat() if order.order_date else None
        } for order in sample_orders]

        return jsonify({
            'status_counts': {status: count for status, count in status_counts},
            'sample_orders': sample_data
        })
    except Exception as e:
        print(f"Error in debug_orders: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update an order's status"""
    try:
        data = request.json
        new_status = data.get('status')

        if not new_status:
            return jsonify({'error': 'No status provided'}), 400

        session = Session()
        order = session.query(Order).get(order_id)

        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # Update order status
        order.status = new_status
        session.commit()

        return jsonify({
            'success': True,
            'message': f'Order status updated to {new_status}'
        })
    except Exception as e:
        session.rollback()
        print(f"Error updating order status: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/performance', methods=['GET'])
def get_performance_metrics():
    """Get performance metrics for dashboard directly from database"""
    try:
        session = Session()

        top_suppliers = session.query(
            Supplier.id,
            Supplier.name,
            Supplier.reliability_score,
            Supplier.quality_score
        ).order_by(Supplier.reliability_score.desc()).limit(5).all()

        top_suppliers_data = []
        for supplier in top_suppliers:
            order_count = session.query(Order).filter(Order.supplier_id == supplier.id).count()

            top_suppliers_data.append({
                'id': supplier.id,
                'name': supplier.name,
                'reliability_score': supplier.reliability_score,
                'quality_score': supplier.quality_score,
                'total_orders': order_count
            })

        total_items = session.query(func.sum(Inventory.quantity)).scalar() or 0

        total_value = session.query(
            func.sum(Inventory.price_per_unit * Inventory.quantity)
        ).scalar() or 0

        low_stock_query = session.query(
            Inventory.location
        ).filter(
            Inventory.quantity < Inventory.min_threshold
        ).group_by(Inventory.location).all()

        low_stock_locations = [loc[0] for loc in low_stock_query]

        inventory_status = {
            'total_items': total_items,
            'low_stock_locations': low_stock_locations,
            'total_value': float(total_value)
        }

        device_distribution = session.query(
            Inventory.device_type,
            func.sum(1).label('quantity')
        ).group_by(Inventory.device_type).all()

        device_distribution_data = []
        total_devices = sum(device.quantity for device in device_distribution)

        for device in device_distribution:
            sales_percentage = float(device.quantity) / total_devices if total_devices > 0 else 0
            device_distribution_data.append({
                'device_type': device.device_type,
                'quantity': device.quantity,
                'sales_percentage': sales_percentage
            })

        current_date = datetime.now()
        start_date = current_date - timedelta(days=365)

        monthly_orders_query = session.query(
            func.strftime('%Y-%m', Order.order_date).label('month'),
            func.count(Order.id).label('order_count'),
            func.sum(Order.total_cost).label('revenue')
        ).filter(
            Order.order_date >= start_date
        ).group_by('month').order_by('month').all()

        monthly_orders = []
        month_dict = {result.month: {'order_count': result.order_count, 'revenue': float(result.revenue or 0)}
                      for result in monthly_orders_query}

        for i in range(12):
            month_date = current_date - timedelta(days=30 * i)
            month_key = month_date.strftime('%Y-%m')
            month_name = month_date.strftime('%b')  # Jan, Feb, etc.

            if month_key in month_dict:
                monthly_orders.append({
                    'month': month_name,
                    'order_count': month_dict[month_key]['order_count'],
                    'revenue': month_dict[month_key]['revenue']
                })
            else:
                monthly_orders.append({
                    'month': month_name,
                    'order_count': 0,
                    'revenue': 0.0
                })

        monthly_orders.reverse()

        department_distribution = session.query(
            Employee.department,
            func.count(Employee.id).label('count')
        ).group_by(Employee.department).all()

        department_data = [
            {'department': dept.department, 'count': dept.count}
            for dept in department_distribution
        ]

        asset_status_query = session.query(
            EmployeeAsset.status,
            func.count(EmployeeAsset.id).label('count')
        ).group_by(EmployeeAsset.status).all()

        asset_status_data = [
            {'status': status.status, 'count': status.count}
            for status in asset_status_query
        ]

        available_count = session.query(Inventory).filter(
            Inventory.status == 'available'
        ).count()

        if available_count > 0:
            asset_status_data.append({
                'status': 'available',
                'count': available_count
            })

        return jsonify({
            'top_suppliers': top_suppliers_data,
            'inventory_status': inventory_status,
            'device_distribution': device_distribution_data,
            'order_trends': monthly_orders,
            'department_distribution': department_data,
            'asset_status': asset_status_data
        })

    except Exception as e:
        print(f"Error in get_performance_metrics: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/employees', methods=['GET'])
def get_employees():
    """Get all employees, optionally filtered by department"""
    department = request.args.get('department', None)

    try:
        session = Session()
        query = session.query(Employee)

        if department and department != 'All':
            query = query.filter(Employee.department == department)

        employees = query.all()

        employees_data = [{
            'id': emp.id,
            'name': emp.name,
            'email': emp.email,
            'department': emp.department,
            'position': emp.position,
            'join_date': emp.join_date.strftime('%Y-%m-%d') if emp.join_date else None
        } for emp in employees]

        departments = ['All'] + [d[0] for d in session.query(Employee.department).distinct()]

        return jsonify({
            'data': employees_data,
            'departments': departments,
            'count': len(employees_data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/employee-assets', methods=['GET'])
def get_employee_assets():
    """Get employee asset assignments, optionally filtered"""
    employee_id = request.args.get('employee_id', None)
    status = request.args.get('status', None)
    department = request.args.get('department', None)
    search_query = request.args.get('search', None)  #

    if request.args.get('statuses') == 'true':
        statuses = ['All', 'active', 'pending_return', 'returned', 'lost', 'damaged']
        return jsonify({'statuses': statuses})

    try:
        session = Session()
        # connect Employee, EmployeeAsset and Inventory table
        query = session.query(
            EmployeeAsset, Employee, Inventory
        ).join(
            Employee, EmployeeAsset.employee_id == Employee.id
        ).join(
            Inventory, EmployeeAsset.inventory_id == Inventory.id
        )

        if employee_id:
            query = query.filter(EmployeeAsset.employee_id == employee_id)
        if status and status != 'All':
            query = query.filter(EmployeeAsset.status == status)
        if department and department != 'All':
            query = query.filter(Employee.department == department)

        if search_query and search_query.strip():
            search_pattern = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    Employee.name.ilike(search_pattern),
                    Inventory.device_name.ilike(search_pattern),
                    Inventory.device_type.ilike(search_pattern)
                )
            )

        results = query.all()

        assets_data = [{
            'id': asset.id,
            'employee_id': asset.employee_id,
            'employee_name': employee.name,
            'department': employee.department,
            'device_name': inventory.device_name,
            'device_type': inventory.device_type,
            'assignment_date': asset.assignment_date.strftime('%Y-%m-%d'),
            'expected_return_date': asset.expected_return_date.strftime(
                '%Y-%m-%d') if asset.expected_return_date else None,
            'actual_return_date': asset.actual_return_date.strftime('%Y-%m-%d') if asset.actual_return_date else None,
            'status': asset.status,
            'notes': asset.notes
        } for asset, employee, inventory in results]

        statuses = ['All', 'active', 'pending_return', 'returned', 'lost', 'damaged']

        return jsonify({
            'data': assets_data,
            'statuses': statuses,
            'count': len(assets_data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/employee-assets', methods=['POST'])
def create_asset_assignment():
    """Create a new asset assignment"""
    data = request.json

    try:
        session = Session()

        existing_assignment = session.query(EmployeeAsset).filter(
            EmployeeAsset.inventory_id == data['inventory_id'],
            EmployeeAsset.status == 'active'
        ).first()

        if existing_assignment:
            return jsonify({'error': 'This device is already assigned to another employee'}), 400

        inventory_item = session.query(Inventory).get(data['inventory_id'])
        if not inventory_item:
            return jsonify({'error': 'Device not found'}), 404

        is_returned_device = False
        if inventory_item.status == 'returned':
            is_returned_device = True

            previous_assignment = session.query(EmployeeAsset).filter(
                EmployeeAsset.inventory_id == data['inventory_id'],
                EmployeeAsset.status == 'returned'
            ).first()

            if previous_assignment:
                previous_assignment.notes += f"\nDevice reassigned on {datetime.now().strftime('%Y-%m-%d')}"

        new_assignment = EmployeeAsset(
            employee_id=data['employee_id'],
            inventory_id=data['inventory_id'],
            assignment_date=datetime.strptime(data['assignment_date'],
                                              '%Y-%m-%d') if 'assignment_date' in data else datetime.now(),
            expected_return_date=datetime.strptime(data['expected_return_date'],
                                                   '%Y-%m-%d') if 'expected_return_date' in data else None,
            status=data.get('status', 'active'),
            notes=data.get('notes', '')
        )

        session.add(new_assignment)

        inventory_item.status = 'active'
        inventory_item.quantity = 0

        session.commit()

        return jsonify({
            'success': True,
            'id': new_assignment.id,
            'message': 'Asset assigned successfully',
            'was_returned': is_returned_device
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/employee-assets/<int:assignment_id>', methods=['PUT'])
def update_asset_assignment(assignment_id):
    """Update an asset assignment (e.g., mark as returned)"""
    data = request.json

    try:
        session = Session()
        assignment = session.query(EmployeeAsset).get(assignment_id)

        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404

        old_status = assignment.status

        if 'status' in data:
            assignment.status = data['status']
        if 'expected_return_date' in data:
            assignment.expected_return_date = datetime.strptime(data['expected_return_date'], '%Y-%m-%d')
        if 'actual_return_date' in data:
            assignment.actual_return_date = datetime.strptime(data['actual_return_date'], '%Y-%m-%d')
        if 'notes' in data:
            assignment.notes = data['notes']

        if 'status' in data and data['status'] == 'returned' and old_status != 'returned':
            inventory_item = session.query(Inventory).get(assignment.inventory_id)
            if inventory_item:
                inventory_item.status = 'available'
                inventory_item.quantity = 1

                if not assignment.actual_return_date:
                    assignment.actual_return_date = datetime.now()

                print(
                    f"Device {inventory_item.device_name} (ID: {inventory_item.id}) marked as available with quantity=1")

        elif 'status' in data and data['status'] in ['damaged', 'lost'] and old_status != data['status']:
            inventory_item = session.query(Inventory).get(assignment.inventory_id)
            if inventory_item:
                inventory_item.status = data['status']
                inventory_item.quantity = 0  #
                print(
                    f"Device {inventory_item.device_name} (ID: {inventory_item.id}) marked as {data['status']} with quantity=0")

        #returned-active or pending_return
        elif 'status' in data and data['status'] in ['active', 'pending_return'] and old_status == 'returned':
            inventory_item = session.query(Inventory).get(assignment.inventory_id)
            if inventory_item:
                inventory_item.status = 'assigned'
                inventory_item.quantity = 0  #
                assignment.actual_return_date = None
                print(
                    f"Device {inventory_item.device_name} (ID: {inventory_item.id}) changed from returned to {data['status']}")

        session.commit()

        return jsonify({
            'success': True,
            'message': 'Asset assignment updated successfully'
        })
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/assets/search', methods=['GET'])
def search_assets():
    """Search for employee assets based on query parameters"""
    try:
        session = Session()

        # 获取查询参数
        search_query = request.args.get('query', '')
        department = request.args.get('department', '')
        status = request.args.get('status', '')

        # 构建基本查询
        query = session.query(
            EmployeeAsset,
            Employee.name.label('employee_name'),
            Employee.department,
            Inventory.device_type,
            Inventory.device_name.label('model')
        ).join(
            Employee, EmployeeAsset.employee_id == Employee.id
        ).join(
            Inventory, EmployeeAsset.inventory_id == Inventory.id
        )

        if search_query:
            query = query.filter(
                or_(
                    Employee.name.ilike(f'%{search_query}%'),
                    Inventory.device_name.ilike(f'%{search_query}%')
                )
            )

        if department and department != 'All Departments':
            query = query.filter(Employee.department == department)

        if status and status != 'All':
            query = query.filter(EmployeeAsset.status == status.lower())

        results = query.all()

        assets_data = []
        for asset, employee_name, department, device_type, model in results:
            assets_data.append({
                'id': asset.id,
                'employee': employee_name,
                'department': department,
                'device_type': device_type,
                'model': model,
                'assignment_date': asset.assignment_date.strftime('%Y-%m-%d') if asset.assignment_date else None,
                'status': asset.status,
                'expected_return_date': asset.expected_return_date.strftime(
                    '%Y-%m-%d') if asset.expected_return_date else None,
                'actual_return_date': asset.actual_return_date.strftime(
                    '%Y-%m-%d') if asset.actual_return_date else None,
                'notes': asset.notes
            })

        return jsonify({
            'data': assets_data,
            'count': len(assets_data)
        })

    except Exception as e:
        print(f"Error in search_assets: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/departments', methods=['GET'])
def get_departments():
    """Get all departments for dropdown filter"""
    try:
        session = Session()
        departments = session.query(Employee.department).distinct().all()
        return jsonify({
            'departments': [dept[0] for dept in departments]
        })
    except Exception as e:
        print(f"Error in get_departments: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/dashboard-summary', methods=['GET'])
def get_dashboard_summary():
    """Get summary data for the dashboard"""
    try:
        session = Session()

        # total_assets
        total_assets = session.query(func.count(Inventory.id)).scalar()

        returned_assets = session.query(func.count(EmployeeAsset.id)).filter(
            EmployeeAsset.status == 'returned'
        ).scalar()

        unassigned_devices = session.query(func.count(Inventory.id)).filter(
            Inventory.quantity > 0
        ).scalar()

        available_devices = unassigned_devices

        pending_requests = session.query(func.count(EmployeeAsset.id)).filter(
            EmployeeAsset.status == 'pending_return'
        ).scalar()

        # total_value
        total_value = session.query(func.sum(
            Inventory.price_per_unit * Inventory.quantity
        )).scalar() or 0

        # dept_stats
        dept_stats = session.query(
            Employee.department,
            func.count(EmployeeAsset.id)
        ).join(
            EmployeeAsset, Employee.id == EmployeeAsset.employee_id
        ).filter(
            EmployeeAsset.status == 'active'
        ).group_by(
            Employee.department
        ).all()

        dept_data = {dept: count for dept, count in dept_stats}

        # STATUS
        status_stats = session.query(
            EmployeeAsset.status,
            func.count(EmployeeAsset.id)
        ).group_by(
            EmployeeAsset.status
        ).all()

        status_data = {status: count for status, count in status_stats}

        # 最近的资产分配
        recent_assignments = session.query(
            EmployeeAsset, Employee, Inventory
        ).join(
            Employee, EmployeeAsset.employee_id == Employee.id
        ).join(
            Inventory, EmployeeAsset.inventory_id == Inventory.id
        ).order_by(
            EmployeeAsset.assignment_date.desc()
        ).limit(10).all()

        recent_data = [{
            'employee_name': emp.name,
            'department': emp.department,
            'device_name': inv.device_name,
            'device_type': inv.device_type,
            'assignment_date': asset.assignment_date.strftime('%Y-%m-%d'),
            'status': asset.status,
            'id': asset.id
        } for asset, emp, inv in recent_assignments]

        return jsonify({
            'total_assets': total_assets,
            'returned_assets': returned_assets,
            'unassigned_devices': unassigned_devices,
            'available_devices': available_devices,
            'pending_requests': pending_requests,
            'total_value': total_value,
            'department_distribution': dept_data,
            'status_distribution': status_data,
            'recent_assignments': recent_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()