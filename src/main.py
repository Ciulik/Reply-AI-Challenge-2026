import os
import pandas as pd
import ulid
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import Langfuse, observe
from langfuse.langchain import CallbackHandler

from risk_engine import build_user_profiles, compute_risk

load_dotenv()

model = ChatOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=5,
)

langfuse_client = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://challenges.reply.com/langfuse")
)


def generate_session_id():
    team = os.getenv("TEAM_NAME", "team").lower().replace(" ", "_")
    return f"{team}_{ulid.new().str}"


def invoke_langchain(system_prompt, user_prompt, session_id):
    handler = CallbackHandler()

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = model.invoke(messages, config={
        "callbacks": [handler],
        "metadata": {"langfuse_session_id": session_id},
    })

    text = response.content.strip()
    return "1" if "1" in text else "0"


@observe()
def analyze_fraud(session_id, prompt):
    system_prompt = "Fraud detection system. Answer ONLY 1 or 0."
    return invoke_langchain(system_prompt, prompt, session_id)


def run_dataset(dataset_path, output_path):
    df = pd.read_csv(dataset_path)

    profiles = build_user_profiles(df)
    session_id = generate_session_id()

    print("RUNNING:", dataset_path)
    print("SESSION:", session_id)

    frauds = []

    for _, row in df.iterrows():
        sender = row["sender_id"]
        profile = profiles.get(sender, {"avg": 1, "known": set()})

        risk = compute_risk(row, profile)

        amount = float(row["amount"])
        avg = profile.get("avg", 1)

        if amount > avg * 10:
            decision = "1"

        elif amount > 20000:
            decision = "1"

        elif risk >= 4:
            decision = "1"

        elif row["recipient_id"] not in profile.get("known", set()) and amount > avg * 1.5:
            decision = "1"

        elif risk >= 1:
            prompt = f"""
Amount: {amount}
Avg: {avg}
Ratio: {amount/avg:.1f}
Risk: {risk}

Fraud? 1 or 0.
"""
            decision = analyze_fraud(session_id, prompt)

        else:
            decision = "0"

        if decision == "1":
            frauds.append(row["transaction_id"])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        for tx in frauds:
            f.write(tx + "\n")

    langfuse_client.flush()

    print("DONE:", dataset_path, "| frauds:", len(frauds))
    print("Session:", session_id)

    return session_id


def main():
    BASE_PATH = os.path.dirname(os.path.dirname(__file__))

    dataset1 = os.path.join(BASE_PATH, "data", "dataset1_validate", "transactions.csv")
    dataset2 = os.path.join(BASE_PATH, "data", "dataset2_validate", "transactions.csv")
    dataset3 = os.path.join(BASE_PATH, "data", "dataset3_validate", "transactions.csv")

    output1 = os.path.join(BASE_PATH, "output", "output1.txt")
    output2 = os.path.join(BASE_PATH, "output", "output2.txt")
    output3 = os.path.join(BASE_PATH, "output", "output3.txt")

    session1 = run_dataset(dataset1, output1)
    session2 = run_dataset(dataset2, output2)
    session3 = run_dataset(dataset3, output3)

    print("\nALL DONE")
    print("Session1:", session1)
    print("Session2:", session2)
    print("Session3:", session3)


if __name__ == "__main__":
    main()