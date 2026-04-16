import random

def generate_data():
    return {
        "ph": round(random.uniform(6.5, 8.5), 2),
        "tds": random.randint(100, 800),
        "temp": round(random.uniform(20, 35), 1),
        "pressure": round(random.uniform(0.8, 1.2), 2),
        "flow": round(random.uniform(0.1, 1.0), 2),
        "lat": 12.97,
        "lon": 77.59
    }

def water_quality(data):
    if data['ph'] < 6 or data['ph'] > 8:
        return "⚠️ Unsafe pH"
    if data['tds'] > 500:
        return "⚠️ High TDS"
    return "✅ Water Safe"