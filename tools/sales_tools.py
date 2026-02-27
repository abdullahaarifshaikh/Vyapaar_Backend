from datetime import datetime, timedelta
from langchain_core.tools import tool
from core.db import customers_collection, orders_collection, products_collection
from bson.objectid import ObjectId
from typing import List, TypedDict


class OrderLine(TypedDict):
    product_id: str
    quantity: int


@tool
def create_sales_order(customer_id: str, items: List[OrderLine]):
    """
    Creates a sales order, calculates the total price, and deducts items from stock.
    """
    total_amount = 0
    processed_items = []

    try:
        for item in items:
            product = products_collection.find_one({"_id": ObjectId(item["product_id"])})
            if not product:
                return {"status": "error", "message": f"Product ID {item['product_id']} not found."}

            if product["quantity"] < item["quantity"]:
                return {"status": "error", "message": f"Insufficient stock for {product['name']}."}

            # Deduct stock
            products_collection.update_one(
                {"_id": ObjectId(item["product_id"])},
                {"$inc": {"quantity": -item["quantity"]}}
            )

            line_total = product["price"] * item["quantity"]
            total_amount += line_total

            processed_items.append({
                "product_id": str(product["_id"]),
                "product_name": product["name"],
                "quantity": item["quantity"],
                "unit_price": product["price"],
                "line_total": line_total
            })

        # Save the order with a timestamp
        order_data = {
            "customer_id": customer_id,
            "items": processed_items,
            "total_amount": total_amount,
            "status": "completed",
            "created_at": datetime.utcnow()  # <-- Essential for reporting
        }

        result = orders_collection.insert_one(order_data)

        return {
            "status": "success",
            "order_id": str(result.inserted_id),
            "total_amount": total_amount
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@tool
def get_sales_summary(period: str = "today"):
    """
    Gets the total sales revenue and number of orders for a specific period.

    Args:
        period: Must be one of 'today', 'week', 'month', or 'all'.
    """
    now = datetime.utcnow()

    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = datetime.min  # 'all' time

    pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$total_amount"},
            "total_orders": {"$sum": 1}
        }}
    ]

    result = list(orders_collection.aggregate(pipeline))

    if result:
        return {
            "status": "success",
            "period": period,
            "total_revenue": result[0]["total_revenue"],
            "total_orders": result[0]["total_orders"]
        }
    return {"status": "success", "period": period, "total_revenue": 0, "total_orders": 0}


@tool
def get_top_products(limit: int = 5):
    """
    Gets the top-selling products based on the total quantity sold across all orders.
    """
    pipeline = [
        {"$unwind": "$items"},  # Break down orders into individual items
        {"$group": {
            "_id": "$items.product_id",
            "product_name": {"$first": "$items.product_name"},
            "total_quantity_sold": {"$sum": "$items.quantity"},
            "total_revenue_generated": {"$sum": "$items.line_total"}
        }},
        {"$sort": {"total_quantity_sold": -1}},  # Sort highest to lowest
        {"$limit": limit}
    ]

    results = list(orders_collection.aggregate(pipeline))
    return {"status": "success", "top_products": results}

# Include add_customer and find_customer from the previous step here if you still want basic customer tagging for orders.