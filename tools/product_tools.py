from langchain_core.tools import tool
from core.db import products_collection
from bson.objectid import ObjectId


@tool
def add_product(name: str, price: float, cost: float, quantity: int = 0, expiry_date: str = None):
    """
    Creates a new product in the inventory database.
    Args:
        name: Name of the product.
        price: Selling price.
        cost: Cost price.
        quantity: Initial stock quantity.
        expiry_date: Optional expiry date (preferably in YYYY-MM-DD format).
    """
    existing = products_collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
    if existing:
        return {
            "status": "error",
            "message": f"Product '{name}' already exists.",
            "product_id": str(existing["_id"])
        }

    product_data = {
        "name": name,
        "price": price,
        "cost": cost,
        "quantity": quantity
    }

    # Only add expiry_date to the document if it was provided
    if expiry_date:
        product_data["expiry_date"] = expiry_date

    result = products_collection.insert_one(product_data)

    response = {
        "status": "success",
        "product_id": str(result.inserted_id),
        "quantity": quantity
    }
    if expiry_date:
        response["expiry_date"] = expiry_date

    return response


@tool
def find_products(search_term: str):
    """
    Searches for products in the inventory by name.
    """
    # Case-insensitive search using regex
    query = {"name": {"$regex": search_term, "$options": "i"}}
    products = list(products_collection.find(query))

    if not products:
        return {"status": "not_found", "message": f"No products found for '{search_term}'."}

    # Convert ObjectIds to strings for JSON serialization
    for p in products:
        p["_id"] = str(p["_id"])

    return {"status": "success", "products": products}


@tool
def update_stock(product_id: str, quantity_to_add: int):
    """
    Updates the stock quantity of an existing product.
    Use a negative number to reduce stock.
    """
    try:
        result = products_collection.find_one_and_update(
            {"_id": ObjectId(product_id)},
            {"$inc": {"quantity": quantity_to_add}},
            return_document=True
        )
        if result:
            result["_id"] = str(result["_id"])
            return {"status": "success", "new_quantity": result["quantity"], "product": result}
        return {"status": "error", "message": "Product not found."}
    except Exception as e:
        return {"status": "error", "message": str(e)}