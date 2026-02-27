from langchain_google_genai import ChatGoogleGenerativeAI
from tools import tools

# Initialize Gemini Model
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# Bind the MongoDB tools to the model
model_with_tools = model.bind_tools(tools)
