import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import ulid
from langfuse import Langfuse, observe
from langfuse.langchain import CallbackHandler

load_dotenv()

model = ChatOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=50,
)

langfuse_client = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://challenges.reply.com/langfuse")
)


def generate_session_id():
    team = os.getenv("TEAM_NAME", "tutorial").replace(" ", "-")
    return f"{team}-{ulid.new().str}"


def invoke_langchain(model, prompt, langfuse_handler, session_id):
    messages = [HumanMessage(content=prompt)]
    response = model.invoke(messages, config={
        "callbacks": [langfuse_handler],
        "metadata": {"langfuse_session_id": session_id},
    })
    return response.content


@observe()

def analyze_fraud(session_id, model, transaction_data):
    langfuse_handler = CallbackHandler()
    
    # System prompt based on MirrorPay mission
    system_prompt = """
    You are a Fraud Detection Agent for MirrorPay. 
    Analyze the transaction details and context. 
    Respond ONLY with '1' if the transaction is FRAUDULENT, or '0' if it is LEGITIMATE.
    Target: Detect Mirror Hackers who shift habits, locations, and amounts. 
    Decision: '1' (Fraud) or '0' (Legit).
    """
    
    return invoke_langchain(model, system_prompt, transaction_data, langfuse_handler, session_id)
def run_llm_call(session_id, model, prompt):
    langfuse_handler = CallbackHandler()
    return invoke_langchain(model, prompt, langfuse_handler, session_id)


def main():
   # 1. Load Challenge Datasets 
    try:
        transactions_df = pd.read_csv('Transactions.csv')
        # Optional: Load other files if needed for context
        # locations_df = pd.read_csv('Locations.csv')
    except FileNotFoundError:
        print("Error: Ensure Transactions.csv is in the project root.")
        return

    session_id = generate_session_id()
    fraudulent_ids = []

    print(f"Starting analysis for session: {session_id}")

    # 2. Iterate through transactions 
    # For testing, you can use transactions_df.head(20)
    for index, row in transactions_df.iterrows():
        # Convert row to a string context for the agent
        tx_context = row.to_string()
        
        # Get AI Decision
        decision = analyze_fraud(session_id, model, tx_context)
        
        # 3. Collect suspected Fraudulent IDs 
        if '1' in decision:
            fraudulent_ids.append(row['Transaction ID'])
            print(f"TX {row['Transaction ID']}: FRAUD DETECTED")
        else:
            print(f"TX {row['Transaction ID']}: LEGITIMATE")

    # 4. Save Output File as ASCII .txt 
    with open('output.txt', 'w') as f:
        for tx_id in fraudulent_ids:
            f.write(f"{tx_id}\n")

    # Finalize Langfuse Trace 
    langfuse_client.flush()
    print(f"\nAnalysis complete. Found {len(fraudulent_ids)} frauds.")
    print(f"Output saved to output.txt. Session ID: {session_id}")

if __name__ == "__main__":
    main()
