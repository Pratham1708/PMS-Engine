def train_gru(

    model,

    X_train,

    y_train,

    class_weights,

    epochs=20,

    batch_size=128
):

    history = model.fit(

        X_train,

        y_train,

        validation_split=0.2,

        epochs=epochs,

        batch_size=batch_size,

        class_weight=class_weights,

        verbose=1
    )

    return history