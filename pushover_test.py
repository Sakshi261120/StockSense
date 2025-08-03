import requests

user_key = "umqpi3kryezvwo9mjpqju5qc5j59kx"
api_token = "aue6x29a79caihi7pt4g27yoef4vv3"
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

