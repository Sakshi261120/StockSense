# alert_logic.py

def check_low_stock(data, threshold=20):
    """
    Returns the subset of data where stock is below the threshold.
    """
    return data[data["Stock_Remaining"] < threshold]

def check_expiry(data, days=7):
    """
    Returns the subset of data where days to expiry is less than or equal to the given days.
    """
    return data[data["Days_To_Expiry"] <= days]

