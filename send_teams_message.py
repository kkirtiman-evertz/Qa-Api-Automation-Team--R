import requests

# Replace with your Microsoft Teams webhook URL
webhook_url = "https://evertz1.webhook.office.com/webhookb2/33be58bf-bed8-4287-bd32-7b739fd3a2f6@e7ca1d1b-0b74-449f-8cc2-a9865bfc0a5f/IncomingWebhook/3fd543a567cb4d55ad46646ef1a798e2/bb4014fc-682b-4603-bb76-e94aff3c8d10"

# Message to send
message = {
    "text": "Hello from Python!",
}

# Send the message using a POST request
try:
    response = requests.post(webhook_url, json=message)
    
    # Check if the request was successful
    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"An error occurred: {e}")
