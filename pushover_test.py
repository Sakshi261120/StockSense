import requests

user_key = "YOUR_PUSHOVER_USER_KEY"
api_token = "YOUR_PUSHOVER_API_TOKEN"
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

