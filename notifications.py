# notification.py
import http.client
import urllib

def send_notification(title, message):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request(
        "POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": "aue6x29a79caihi7pt4g27yoef4vv3",     # Replace with your app token
            "user": "umqpi3kryezvwo9mjpqju5qc5j59kx",       # Replace with your user key
            "title": title,
            "message": message,
        }),
        {"Content-type": "application/x-www-form-urlencoded"}
    )
    res = conn.getresponse()
    print(res.status, res.read())




