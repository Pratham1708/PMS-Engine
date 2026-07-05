from sklearn.metrics import (

    classification_report,

    confusion_matrix,

    accuracy_score
)


def evaluate_model(

    model,

    encoder,

    X_test,

    y_test
):

    preds = model.predict(
        X_test
    )

    decoded = encoder.inverse_transform(
        preds
    )

    report = classification_report(

        y_test,

        decoded,

        output_dict=False
    )

    accuracy = accuracy_score(

        y_test,

        decoded
    )

    matrix = confusion_matrix(

        y_test,

        decoded
    )

    return {

        "accuracy": accuracy,

        "report": report,

        "confusion_matrix": matrix
    }