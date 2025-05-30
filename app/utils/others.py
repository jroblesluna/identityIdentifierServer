import numpy as np

def convert_numpy_types(obj):
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, set):
        return {convert_numpy_types(item) for item in obj}
    elif isinstance(obj, np.generic):
        return obj.item()  # convierte np.bool_, np.int32, etc. a bool, int, float
    else:
        return obj