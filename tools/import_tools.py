import pandas as pd
from langchain_core.tools import tool
from core.db import products_collection
import os

@tool
def import_inventory_from_excel(file_path: str):
    """
    Imports inventory items from an Excel file into the database.
    The Excel sheet should have headers: name, price, cost, quantity.
    """
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"File not found: {file_path}"}
    
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Normalize column names (strip whitespace and lowercase)
        df.columns = [col.strip().lower() for col in df.columns]
        
        required_columns = ["name", "price", "cost", "quantity"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                "status": "error", 
                "message": f"Missing required columns in Excel: {', '.join(missing_columns)}"
            }
        
        added_count = 0
        updated_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                name = str(row["name"]).strip()
                price = float(row["price"])
                cost = float(row["cost"])
                quantity = int(row["quantity"])
                
                # Use add_product style logic
                existing = products_collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
                
                if existing:
                    # Update stock and price/cost if already exists
                    products_collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": {"price": price, "cost": cost}, "$inc": {"quantity": quantity}}
                    )
                    updated_count += 1
                else:
                    # Insert new
                    product_data = {
                        "name": name,
                        "price": price,
                        "cost": cost,
                        "quantity": quantity
                    }
                    products_collection.insert_one(product_data)
                    added_count += 1
            except Exception as row_error:
                errors.append(f"Row {index + 2}: {str(row_error)}")
        
        result_message = f"Import completed: {added_count} products added, {updated_count} products updated."
        if errors:
            result_message += f" Encountered {len(errors)} errors."
            
        return {
            "status": "success",
            "message": result_message,
            "added": added_count,
            "updated": updated_count,
            "errors": errors
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to process Excel file: {str(e)}"}
