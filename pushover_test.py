import requests

user_key = ""
api_token = ""
message = "Hello from Pushover test!"

response = requests.post(
    "https://api.pushover.net/1/messages.json",
    data={
        "token": api_token,
        "user": user_key,
        "message": message,
    }
)

print("Status code:", response.status_code)
print("Response:", response.text)

