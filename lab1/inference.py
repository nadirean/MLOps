import joblib


def load_model(path="model.joblib"):
    return joblib.load(path)


def predict(model, data):
    prediction = model.predict([data])[0]
    class_names = ["setosa", "versicolor", "virginica"]
    return class_names[prediction]
