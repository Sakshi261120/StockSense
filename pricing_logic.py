# pricing_logic.py
import pickle
import numpy as np

def load_model(path='demand_model.pkl'):
    """
    Load the trained machine learning model from a pickle file.
    """
    with open(path, 'rb') as f:
        model = pickle.load(f)
    return model

def predict_price(quantity, model):
    """
    Predict the optimal unit price for a given quantity sold.
    """
    predicted_price = model.predict(np.array([[quantity]]))[0]
    return round(predicted_price, 2)

