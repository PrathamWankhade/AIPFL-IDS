import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.regularizers import l2
from tensorflow.keras.optimizers import Adam

import config


def create_model(input_dim, num_classes, strategy=None):
    if strategy is None:
        strategy = tf.distribute.get_strategy()

    with strategy.scope():
        model = Sequential(name="AIPFL_IDS_DNN")

        units = config.DENSE_UNITS
        drops = config.DROPOUT_RATES

        for i, u in enumerate(units):
            if i == 0:
                model.add(Dense(u, activation="relu", kernel_regularizer=l2(config.L2_REG), input_shape=(input_dim,), name=f"dense_{u}"))
            else:
                model.add(Dense(u, activation="relu", kernel_regularizer=l2(config.L2_REG), name=f"dense_{u}"))
            model.add(BatchNormalization(name=f"bn_{u}"))
            if i < len(drops):
                model.add(Dropout(drops[i], name=f"dropout_{u}"))

        model.add(Dense(num_classes, activation="softmax", dtype="float32", name="output"))

        optimizer = Adam(learning_rate=config.LEARNING_RATE, clipnorm=config.CLIPNORM)
        model.compile(optimizer=optimizer, loss="sparse_categorical_crossentropy", metrics=["accuracy"])

    return model


def get_client_callbacks():
    return [
        tf.keras.callbacks.EarlyStopping(monitor="loss", patience=config.EARLY_STOPPING_PATIENCE, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="loss", factor=config.REDUCE_LR_FACTOR, patience=config.REDUCE_LR_PATIENCE, min_lr=config.MIN_LR, verbose=0),
    ]
