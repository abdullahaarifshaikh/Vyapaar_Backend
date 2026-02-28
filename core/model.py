from langchain_openai import ChatOpenAI
from config.settings import SARV_API
from tools import tools

# Initialize Sarvam AI Model via OpenAI-Compatible API
# Note: sarvam-m doesn't support native tool calling, so we'll handle it via prompting
model = ChatOpenAI(
    model="sarvam-m",
    api_key=SARV_API,
    base_url="https://api.sarvam.ai/v1",
    temperature=0
)

# We still need the list of tools for reference
# But we won't bind them natively if the model doesn't support it.
# However, to keep the graph logic similar, we will simulate the behavior.
# Actually, let's keep model_with_tools pointing to the model for now, 
# and handle the "binding" logic in the prompt and workflow.
model_with_tools = model 
