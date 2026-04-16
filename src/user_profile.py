class UserProfile:

    def __init__(self, user_id):
        self.user_id = user_id
        self.transactions = []
        self.known_recipients = set()
        self.amounts = []
        self.types = []

    def update(self, transaction):
        self.transactions.append(transaction)
        self.known_recipients.add(transaction["recipient_id"])
        self.amounts.append(transaction["amount"])
        self.types.append(transaction["transaction_type"])

    @property
    def avg_amount(self):
        if len(self.amounts) == 0:
            return 0
        return sum(self.amounts) / len(self.amounts)

    @property
    def common_types(self):
        return set(self.types)