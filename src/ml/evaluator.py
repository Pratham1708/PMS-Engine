from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score
)


def evaluate_model(
    model,
    X_test,
    y_test
):

    preds = model.predict(X_test)

    print(
        "Accuracy:",
        accuracy_score(
            y_test,
            preds
        )
    )

    print(
        classification_report(
            y_test,
            preds
        )
    )

    print(
        confusion_matrix(
            y_test,
            preds
        )
    )

    return preds