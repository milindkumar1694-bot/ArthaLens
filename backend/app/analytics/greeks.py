from math import erf, exp, log, pi, sqrt

def calculate_greeks(spot: float | None, strike: float, iv: float | None, days: float, is_call: bool, rate: float, dividend: float = 0.0) -> dict | None:
    if spot is None or iv is None or min(spot, strike, iv, days) <= 0: return None
    t, sigma = days/365, iv/100; d1 = (log(spot/strike)+(rate-dividend+sigma*sigma/2)*t)/(sigma*sqrt(t)); d2 = d1-sigma*sqrt(t)
    cdf = lambda x: (1+erf(x/sqrt(2)))/2; pdf = exp(-d1*d1/2)/sqrt(2*pi)
    delta = exp(-dividend*t)*(cdf(d1) if is_call else cdf(d1)-1)
    theta = (-(spot*exp(-dividend*t)*pdf*sigma)/(2*sqrt(t)) - (rate*strike*exp(-rate*t)*(cdf(d2) if is_call else cdf(-d2))) + (dividend*spot*exp(-dividend*t)*(cdf(d1) if is_call else cdf(-d1))))/365
    return {"delta": round(delta, 5), "gamma": round(exp(-dividend*t)*pdf/(spot*sigma*sqrt(t)), 8), "theta": round(theta, 5), "vega": round(spot*exp(-dividend*t)*pdf*sqrt(t)/100, 5)}
