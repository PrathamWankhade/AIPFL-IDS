import random
import warnings

import numpy as np
import tensorflow as tf
from tensorflow.keras import mixed_precision

import config

warnings.filterwarnings("ignore")


def set_seeds(seed=None):
    if seed is None:
        seed = config.SEED
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def configure_gpu():
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        strategy = tf.distribute.MirroredStrategy()
        print(f"GPUs detected: {strategy.num_replicas_in_sync}")
    else:
        strategy = tf.distribute.get_strategy()
        print("No GPU detected. Using CPU.")
    return strategy


def enable_mixed_precision():
    mixed_precision.set_global_policy(config.MIXED_PRECISION)


def setup_environment():
    set_seeds()
    strategy = configure_gpu()
    enable_mixed_precision()
    print(f"TensorFlow {tf.__version__} | NumPy {np.__version__}")
    return strategy
