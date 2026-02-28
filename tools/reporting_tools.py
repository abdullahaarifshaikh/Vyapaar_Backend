import os
import matplotlib.pyplot as plt
plt.switch_backend('Agg')
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
from langchain_core.tools import tool
from core.db import orders_collection, products_collection
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

@tool
def generate_sales_dashboard_pdf(period: str = "week") -> str:
    """
    Generates a PDF sales dashboard with graphs for a specific period.
    Supported periods: 'daily', 'weekly', 'monthly', 'yearly'.
    Returns the absolute path to the generated PDF.
    """
    now = datetime.utcnow()
    
    if period == "daily":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        title_period = "Daily"
    elif period == "weekly":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        title_period = "Weekly"
    elif period == "monthly":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        title_period = "Monthly"
    elif period == "yearly":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        title_period = "Yearly"
    else:
        # Default to weekly if invalid period
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        title_period = "Weekly"

    # 1. Fetch data from MongoDB
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date}}},
        {"$unwind": "$items"}
    ]
    orders = list(orders_collection.aggregate(pipeline))
    
    if not orders:
        return f"No sales data found for the {period} period."

    # 2. Process data with Pandas for easy plotting
    data = []
    # Map product IDs to their costs to calculate profit
    product_costs = {str(p['_id']): p.get('cost', 0) for p in products_collection.find()}
    
    for o in orders:
        item = o['items']
        pid = item['product_id']
        cost = product_costs.get(pid, 0)
        revenue = item['line_total']
        profit = revenue - (cost * item['quantity'])
        
        data.append({
            "Product": item['product_name'],
            "Sales": revenue,
            "Profit": profit,
            "Quantity": item['quantity']
        })
    
    df = pd.DataFrame(data)
    summary = df.groupby("Product").agg({
        "Sales": "sum",
        "Profit": "sum",
        "Quantity": "sum"
    }).reset_index()

    # 3. Generate Charts using Matplotlib
    os.makedirs("reports/tmp", exist_ok=True)
    file_prefix = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sales Chart
    plt.figure(figsize=(10, 5))
    plt.bar(summary["Product"], summary["Sales"], color='skyblue')
    plt.title(f"{title_period} Sales by Product")
    plt.xlabel("Product")
    plt.ylabel("Sales Amount ($)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    sales_img_path = f"reports/tmp/sales_{file_prefix}.png"
    plt.savefig(sales_img_path)
    plt.close()

    # Profit Chart
    plt.figure(figsize=(10, 5))
    plt.bar(summary["Product"], summary["Profit"], color='salmon')
    plt.title(f"{title_period} Profit by Product")
    plt.xlabel("Product")
    plt.ylabel("Profit Amount ($)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    profit_img_path = f"reports/tmp/profit_{file_prefix}.png"
    plt.savefig(profit_img_path)
    plt.close()

    # 4. Create PDF using ReportLab
    pdf_path = os.path.abspath(f"reports/Sales_Dashboard_{title_period}_{file_prefix}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"Sales Dashboard - {title_period}", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Period Starting: {start_date.strftime('%Y-%m-%d')}", styles['Normal']))
    elements.append(Paragraph(f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 24))

    # Summary Table
    table_data = [["Product", "Quantity Sold", "Total Sales", "Total Profit"]]
    for _, row in summary.iterrows():
        table_data.append([
            row["Product"],
            str(row["Quantity"]),
            f"${row['Sales']:.2f}",
            f"${row['Profit']:.2f}"
        ])
    
    # Add Totals
    table_data.append([
        "TOTAL",
        str(summary["Quantity"].sum()),
        f"${summary['Sales'].sum():.2f}",
        f"${summary['Profit'].sum():.2f}"
    ])

    summary_table = Table(table_data, colWidths=[2.5*inch, 1*inch, 1.2*inch, 1.2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 24))

    # Add Charts
    elements.append(Paragraph("Sales Analysis", styles['Heading2']))
    elements.append(Image(sales_img_path, width=6*inch, height=3*inch))
    elements.append(Spacer(1, 24))
    
    elements.append(Paragraph("Profit Analysis", styles['Heading2']))
    elements.append(Image(profit_img_path, width=6*inch, height=3*inch))

    # Build PDF
    doc.build(elements)

    # Cleanup temporary images
    os.remove(sales_img_path)
    os.remove(profit_img_path)

    return pdf_path
