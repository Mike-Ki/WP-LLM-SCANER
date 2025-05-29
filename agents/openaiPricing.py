openai_pricing = {
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "gpt-3.5-turbo-instruct": {"input": 1.50, "output": 2.00},
    "gpt-3.5-turbo-16k-0613": {"input": 3.00, "output": 4.00},
    "codex-mini-latest": {"input": 1.50, "output": 6.00}
}

def estimated_price(model_prices):
    return sum(price for price in model_prices.values() if price is not None)


def get_model_estimated_price(model_name: str):
    key = model_name.strip().lower()
    pricing_lookup = {k.lower(): v for k, v in openai_pricing.items()}
    prices = pricing_lookup.get(key)
    if prices is None:
        return None
    return estimated_price(prices)


def sorted_model_prices():
    estimated_prices = [
        (model, estimated_price(prices))
        for model, prices in openai_pricing.items()
    ]

    return sorted(estimated_prices, key=lambda x: x[1], reverse=True)



if __name__ == "__main__":
    print("Model Pricing Estimate for 1M tokens (most expensive first):\n")
    for model, price in  sorted_model_prices():
        print(f"{model:30}: ${price:.2f}")