import numpy as np

def buffer_to_array(buffer, dtype=np.int16):
    return np.frombuffer(buffer, dtype=dtype) 

def normalize(arr):
    return arr.astype(np.float32) / np.iinfo(np.int16).max
