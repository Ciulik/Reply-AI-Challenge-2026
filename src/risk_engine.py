def build_user_profiles(df):
    profiles = {}

    for _, row in df.iterrows():
        user = row["sender_id"]
        amount = row["amount"]
        recipient = row["recipient_id"]

        if user not in profiles:
            profiles[user] = {
                "total": 0,
                "count": 0,
                "known": set()
            }

        profiles[user]["total"] += amount
        profiles[user]["count"] += 1
        profiles[user]["known"].add(recipient)

    for user in profiles:
        profiles[user]["avg"] = profiles[user]["total"] / profiles[user]["count"]

    return profiles


def compute_risk(row, profile):
    risk = 0

    amount = float(row["amount"])
    avg = profile.get("avg", 1)

    if amount > avg * 4:
        risk += 3

    if amount > avg * 10:
        risk += 5

    if amount > 10000:
        risk += 2

    try:
        hour = int(row["timestamp"].split("T")[1].split(":")[0])
        if hour < 5:
            risk += 2
    except:
        pass

    if row["transaction_type"] not in ["bank transfer"]:
        risk += 1

    if row["recipient_id"] not in profile.get("known", set()):
        risk += 2

    return risk