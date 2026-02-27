from langchain_core.messages import HumanMessage, SystemMessage
from core.workflow import build_workflow

SYSTEM_PROMPT = """
You are AnyConnect — an AI-powered business assistant designed to help store owners manage inventory and track sales data.
You operate through natural language instructions that feel conversational, like a WhatsApp chat.

Your role:
- Manage Inventory: Use tools like `add_product`, `find_products`, and `update_stock` to keep the warehouse updated.
- Manage Sales: Use `create_sales_order` to check out items and deduct stock.
- Report Insights: Use `get_sales_summary` and `get_top_products` to answer questions like "How much did we make today?" or "What are our best sellers?"
- Always explain actions and reports clearly, concisely, and professionally. Use bullet points for reports to make them easy to read.
- Never display raw database IDs (like MongoDB ObjectIds) to the user.

Tone:
- Friendly, helpful, and business-smart.
- Prioritize clarity and brevity — Business users prefer short, actionable replies with clear metrics.
"""

if __name__ == "__main__":
    app = build_workflow()
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    print("🤖 Inventory & Sales Reports Agent ready. Type 'quit' to exit.\n")

    while True:
        user = input("👤 You: ")
        if user.lower() in ["quit", "exit"]:
            break

        messages.append(HumanMessage(content=user))
        result = app.invoke({"messages": messages})

        ai_response = result["messages"][-1]

        # Check if the content is a list of blocks (like the one with the signature)
        if isinstance(ai_response.content, list):
            # Safely extract just the 'text' value from the first block
            text = ai_response.content[0].get('text', '')
        else:
            # If it's already a normal string, just use it
            text = str(ai_response.content)

        if text:
            print(f"🤖 {text}\n")

        messages.append(ai_response)