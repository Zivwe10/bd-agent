import json
import os
from datetime import datetime
from collections import defaultdict

# Path to data files
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
orders_file = os.path.join(data_dir, 'orders.json')
order_lines_file = os.path.join(data_dir, 'order_lines.json')

# ============================================================================
# CORE DATA LOADING FUNCTIONS
# ============================================================================

def load_orders():
    """Load all orders from JSON file."""
    try:
        with open(orders_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Orders file not found at {orders_file}")
        return []

def load_order_lines():
    """Load all order line items from JSON file."""
    try:
        with open(order_lines_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Order lines file not found at {order_lines_file}")
        return []

def get_all_data():
    """Get all orders and order lines together."""
    return {
        'orders': load_orders(),
        'order_lines': load_order_lines()
    }

# ============================================================================
# QUERY AND FILTER FUNCTIONS
# ============================================================================

def get_orders_by_territory(territory):
    """Get all orders for a specific territory."""
    orders = load_orders()
    return [order for order in orders if order['territory'] == territory]

def get_orders_by_status(status):
    """Get all orders with a specific status."""
    orders = load_orders()
    return [order for order in orders if order['status'] == status]

def get_orders_by_territory_and_status(territory, status):
    """Get orders for a territory with a specific status."""
    orders = load_orders()
    return [
        order for order in orders 
        if order['territory'] == territory and order['status'] == status
    ]

def get_order_details(order_id):
    """Get a specific order and all its line items."""
    orders = load_orders()
    order_lines = load_order_lines()
    
    # Find the order
    order = None
    for o in orders:
        if o['order_id'] == order_id:
            order = o
            break
    
    if not order:
        return None
    
    # Find all line items for this order
    lines = [line for line in order_lines if line['order_id'] == order_id]
    
    return {
        'order': order,
        'line_items': lines
    }

def get_orders_by_customer(customer_name):
    """Get all orders from a specific customer."""
    orders = load_orders()
    return [order for order in orders if order['customer_name'] == customer_name]

# ============================================================================
# STATISTICS AND AGGREGATIONS
# ============================================================================

def get_territory_statistics():
    """Get revenue and order counts for each territory."""
    orders = load_orders()
    
    stats = defaultdict(lambda: {'order_count': 0, 'total_revenue': 0, 'orders': []})
    
    for order in orders:
        territory = order['territory']
        stats[territory]['order_count'] += 1
        stats[territory]['total_revenue'] += order['total_amount']
        stats[territory]['orders'].append(order['order_id'])
    
    # Convert to regular dict and add average
    result = {}
    for territory, data in stats.items():
        result[territory] = {
            'order_count': data['order_count'],
            'total_revenue': round(data['total_revenue'], 2),
            'average_order_value': round(data['total_revenue'] / data['order_count'], 2),
            'orders': data['orders']
        }
    
    return result

def get_status_summary():
    """Get order count and revenue by status."""
    orders = load_orders()
    
    summary = defaultdict(lambda: {'count': 0, 'revenue': 0})
    
    for order in orders:
        status = order['status']
        summary[status]['count'] += 1
        summary[status]['revenue'] += order['total_amount']
    
    # Convert to regular dict
    result = {}
    for status, data in summary.items():
        result[status] = {
            'count': data['count'],
            'revenue': round(data['revenue'], 2)
        }
    
    return result

def get_top_customers(limit=5):
    """Get top customers by total order value."""
    orders = load_orders()
    
    customer_totals = defaultdict(float)
    customer_order_counts = defaultdict(int)
    
    for order in orders:
        customer_totals[order['customer_name']] += order['total_amount']
        customer_order_counts[order['customer_name']] += 1
    
    # Sort by total revenue
    sorted_customers = sorted(
        customer_totals.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    result = []
    for customer_name, total_revenue in sorted_customers[:limit]:
        result.append({
            'customer_name': customer_name,
            'total_revenue': round(total_revenue, 2),
            'order_count': customer_order_counts[customer_name]
        })
    
    return result

def get_product_summary():
    """Get product distribution across orders (SKU count, total quantity)."""
    order_lines = load_order_lines()
    
    product_stats = defaultdict(lambda: {'total_quantity': 0, 'total_revenue': 0, 'order_count': 0})
    
    for line in order_lines:
        sku = line['sku']
        product_stats[sku]['total_quantity'] += line['quantity']
        product_stats[sku]['total_revenue'] += line['line_total']
        product_stats[sku]['order_count'] += 1
    
    # Sort by revenue
    sorted_products = sorted(
        product_stats.items(),
        key=lambda x: x[1]['total_revenue'],
        reverse=True
    )
    
    result = []
    for sku, data in sorted_products:
        # Find product name from first occurrence
        order_lines_list = load_order_lines()
        product_name = next(
            (line['product_name'] for line in order_lines_list if line['sku'] == sku),
            'Unknown'
        )
        
        result.append({
            'sku': sku,
            'product_name': product_name,
            'total_quantity': data['total_quantity'],
            'total_revenue': round(data['total_revenue'], 2),
            'appears_in_orders': data['order_count']
        })
    
    return result

# ============================================================================
# REPORTING FUNCTIONS
# ============================================================================

def generate_operational_summary():
    """Generate a complete operational summary."""
    orders = load_orders()
    
    summary = {
        'total_orders': len(orders),
        'total_revenue': round(sum(o['total_amount'] for o in orders), 2),
        'average_order_value': round(
            sum(o['total_amount'] for o in orders) / len(orders), 2
        ) if orders else 0,
        'territory_stats': get_territory_statistics(),
        'status_summary': get_status_summary(),
        'top_customers': get_top_customers(3),
    }
    
    return summary

def generate_territory_report(territory):
    """Generate a detailed report for a specific territory."""
    orders = get_orders_by_territory(territory)
    order_lines = load_order_lines()
    
    if not orders:
        return {'error': f'No orders found for territory: {territory}'}
    
    # Get line items for this territory's orders
    order_ids = [o['order_id'] for o in orders]
    territory_lines = [line for line in order_lines if line['order_id'] in order_ids]
    
    report = {
        'territory': territory,
        'total_orders': len(orders),
        'total_revenue': round(sum(o['total_amount'] for o in orders), 2),
        'average_order_value': round(sum(o['total_amount'] for o in orders) / len(orders), 2),
        'status_breakdown': {},
        'total_line_items': len(territory_lines),
        'total_units_ordered': sum(line['quantity'] for line in territory_lines),
        'orders': [
            {
                'order_id': o['order_id'],
                'customer': o['customer_name'],
                'date': o['order_date'],
                'status': o['status'],
                'amount': o['total_amount']
            }
            for o in orders
        ]
    }
    
    # Add status breakdown
    for order in orders:
        status = order['status']
        if status not in report['status_breakdown']:
            report['status_breakdown'][status] = {'count': 0, 'revenue': 0}
        report['status_breakdown'][status]['count'] += 1
        report['status_breakdown'][status]['revenue'] += order['total_amount']
    
    # Round revenue values in status breakdown
    for status in report['status_breakdown']:
        report['status_breakdown'][status]['revenue'] = round(
            report['status_breakdown'][status]['revenue'], 2
        )
    
    return report

def list_all_territories():
    """Get list of all unique territories."""
    orders = load_orders()
    territories = list(set(o['territory'] for o in orders))
    return sorted(territories)

def list_all_statuses():
    """Get list of all unique order statuses."""
    orders = load_orders()
    statuses = list(set(o['status'] for o in orders))
    return sorted(statuses)

def get_upcoming_shipments(days_ahead=30):
    """Get orders with 'Shipped' status (in-transit orders, upcoming deliveries)."""
    orders = load_orders()
    today = datetime.strptime('2026-04-07', '%Y-%m-%d')
    future_date = datetime(today.year, today.month + (today.day + days_ahead - 1) // 30, 
                           ((today.day + days_ahead - 1) % 30) + 1) if today.month < 12 \
                  else datetime(today.year + 1, 1, 1)
    
    # For simplicity: show all 'Shipped' orders (treating them as upcoming deliveries)
    shipped = [order for order in orders if order['status'] == 'Shipped']
    
    result = []
    for order in shipped:
        order_date = datetime.strptime(order['order_date'], '%Y-%m-%d')
        result.append({
            'order_id': order['order_id'],
            'customer': order['customer_name'],
            'territory': order['territory'],
            'shipped_date': order['order_date'],
            'amount': order['total_amount']
        })
    
    return result

# ============================================================================
# DEMO / TESTING
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("OPERATIONS MANAGER - DATA OVERVIEW")
    print("=" * 70)
    
    # Summary
    summary = generate_operational_summary()
    print(f"\n[OVERALL SUMMARY]")
    print(f"   Total Orders: {summary['total_orders']}")
    print(f"   Total Revenue: ${summary['total_revenue']:,.2f}")
    print(f"   Average Order Value: ${summary['average_order_value']:,.2f}")
    
    # Territory breakdown
    print(f"\n[TERRITORY BREAKDOWN]")
    for territory, stats in summary['territory_stats'].items():
        print(f"\n   {territory}:")
        print(f"      Orders: {stats['order_count']}")
        print(f"      Revenue: ${stats['total_revenue']:,.2f}")
        print(f"      Avg Order: ${stats['average_order_value']:,.2f}")
    
    # Status summary
    print(f"\n[STATUS SUMMARY]")
    for status, data in summary['status_summary'].items():
        print(f"   {status}: {data['count']} orders (${data['revenue']:,.2f})")
    
    # Top customers
    print(f"\n[TOP CUSTOMERS]")
    for i, customer in enumerate(summary['top_customers'], 1):
        print(f"   {i}. {customer['customer_name']}: ${customer['total_revenue']:,.2f} ({customer['order_count']} orders)")
    
    # Upcoming shipments
    print(f"\n[UPCOMING SHIPMENTS (In Transit)]")
    upcoming = get_upcoming_shipments()
    if upcoming:
        for shipment in upcoming:
            print(f"   {shipment['order_id']} - {shipment['customer']} ({shipment['territory']}): ${shipment['amount']}")
    else:
        print("   No upcoming shipments")
    
    print("\n" + "=" * 70)
