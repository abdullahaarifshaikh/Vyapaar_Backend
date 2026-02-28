from .product_tools import add_product, find_products, update_stock, delete_product
from .sales_tools import (
    create_sales_order,
    get_sales_summary,
    get_top_products
)
from .audio_tools import process_audio_file
from .reporting_tools import generate_sales_dashboard_pdf

# Added the reporting tools to the list
tools = [
    add_product,
    find_products,
    update_stock,
    delete_product,
    create_sales_order,
    get_sales_summary,
    get_top_products,
    process_audio_file,
    generate_sales_dashboard_pdf
]