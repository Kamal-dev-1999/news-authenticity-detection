# core/model.py
from django.conf import settings
import os
import pickle
import warnings
from sklearn.exceptions import InconsistentVersionWarning

# Initialize models at module level
try:
    # Define model paths using BASE_DIR
    models_dir = os.path.join(settings.BASE_DIR, "models")
    nb_model_path = os.path.join(models_dir, "nb_model.pkl")
    vect_model_path = os.path.join(models_dir, "vectorizer_model.pkl")

    # Verify model directory exists
    if not os.path.exists(models_dir):
        raise FileNotFoundError(f"Models directory not found at {models_dir}")

    # Load models with version warning suppression
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InconsistentVersionWarning)
        
        # Load Naive Bayes model
        with open(nb_model_path, "rb") as nb_file:
            nb_model = pickle.load(nb_file)
        
        # Load Vectorizer model
        with open(vect_model_path, "rb") as vect_file:
            vect_model = pickle.load(vect_file)

except Exception as e:
    # Handle initialization errors
    nb_model = None
    vect_model = None
    raise ImportError(f"Failed to load models: {str(e)}")

def get_models():
    """Return both models with error handling"""
    if nb_model is None or vect_model is None:
        raise RuntimeError("Models not initialized properly")
    return nb_model, vect_model