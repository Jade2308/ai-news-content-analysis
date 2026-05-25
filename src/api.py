import requests

API_KEY = "AIzaSyDxbTsAhQs3n3v1Lzh6z2kvdAxWkBr651E"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

response = requests.get(url)
models = response.json()

for model in models.get("models", []):
    print(model["name"], "-", model.get("displayName", ""))