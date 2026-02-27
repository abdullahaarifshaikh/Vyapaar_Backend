from .product_tools import add_product, find_products, update_stock
from .sales_tools import (
    create_sales_order,
    get_sales_summary,
    get_top_products
)

# Added the reporting tools to the list
tools = [
    add_product,
    find_products,
    update_stock,
    create_sales_order,
    get_sales_summary,
    get_top_products
]