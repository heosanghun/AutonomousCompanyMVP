def run(symbol: str = "BTCUSDT", period: int = 14) -> float:
    """
    지정된 심볼의 RSI(상대강도지수)를 계산하여 과매수/과매도 상태를 분석합니다.
    RSI > 70 이면 과매수, RSI < 30 이면 과매도로 판단합니다.
    """
    # 실무 환경에서는 실제 거래소 캔들 데이터를 가져와 계산해야 하지만,
    # 여기서는 데모를 위해 가상의 RSI 값을 생성하여 반환합니다.
    import random
    rsi_value = random.uniform(20.0, 80.0)
    print(f"[Skill: RSI] Analyzing {symbol}... Current RSI: {rsi_value:.2f}")
    return rsi_value
