# Reply-AI-Challenge-2026# Reply Mirror 2026 — Fraud Detection Agent

## Overview
An AI-powered fraud detection system for the Reply Mirror Challenge 2026. The system analyzes financial transactions and classifies them as fraudulent or legitimate using a combination of deterministic risk rules and an LLM-based decision layer.

## Architecture

### `user_profile.py`
Builds behavioral profiles for each user based on their transaction history:
- Tracks known recipients, transaction amounts, and types
- Computes average transaction amount per user
- Used to detect anomalies relative to a user's normal behavior

### `risk_engine.py`
Computes a numeric risk score for each transaction:
- **Amount anomaly**: flags transactions exceeding 5x or 10x the user's average
- **High absolute amount**: flags transactions above €10,000
- **Night activity**: flags transactions between midnight and 5am
- **Unknown recipient**: flags transfers to new recipients
- **Transaction type**: non-bank-transfer types receive higher risk

### `main.py`
Orchestrates the full pipeline:
1. Loads transaction CSV datasets
2. Builds user profiles via `build_user_profiles()`
3. For each transaction, computes risk score
4. Applies hard rules (instant fraud decision) for extreme cases
5. Calls GPT-4o-mini via OpenRouter for medium-risk cases
6. Logs all decisions to Langfuse for observability
7. Writes fraud transaction IDs to output text files

## Decision Logic

```
amount > avg * 10  →  FRAUD (hard rule)
amount > 20,000    →  FRAUD (hard rule)
risk >= 5          →  FRAUD (hard rule)
risk >= 2          →  LLM decision (GPT-4o-mini)
else               →  SAFE
```

## Setup

### Requirements
```
pip install langchain-openai langfuse pandas python-dotenv ulid-py
```

### Environment Variables
Create a `.env` file in the project root:
```
OPENROUTER_API_KEY=your_key_here
LANGFUSE_PUBLIC_KEY=your_key_here
LANGFUSE_SECRET_KEY=your_key_here
LANGFUSE_HOST=https://challenges.reply.com/langfuse
TEAM_NAME=your_team_name
```

### Running
```bash
python src/main.py
```

## Output Format
Each output file is a plain UTF-8 text file with one transaction ID per line:
```
550e8400-e29b-41d4-a716-446655440000
f47ac10b-58cc-4372-a567-0e02b2c3d479
```

## Project Structure
```
├── src/
│   ├── main.py
│   ├── risk_engine.py
│   └── user_profile.py
├── data/
│   ├── dataset1/transactions.csv
│   ├── dataset2/transactions.csv
│   └── dataset3/transactions.csv
├── output/
│   ├── output1.txt
│   ├── output2.txt
│   └── output3.txt
└── .env
```
