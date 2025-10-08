from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
import joblib


def load_data():
    return load_iris(return_X_y=True)


def train_model():
    X, y = load_data()
    model = DecisionTreeClassifier()
    model.fit(X, y)
    return model


def save_model(model, path="model.joblib"):
    joblib.dump(model, path)


if __name__ == "__main__":
    model = train_model()
    save_model(model)
    print("Model trained and saved successfully!")
