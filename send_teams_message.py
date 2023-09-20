import requests

# Replace with your Microsoft Teams webhook URL
webhook_url = "https://evertz1.webhook.office.com/webhookb2/33be58bf-bed8-4287-bd32-7b739fd3a2f6@e7ca1d1b-0b74-449f-8cc2-a9865bfc0a5f/IncomingWebhook/3fd543a567cb4d55ad46646ef1a798e2/bb4014fc-682b-4603-bb76-e94aff3c8d10%22"

# Mention user or team
mention = {
    "type": "mention",
    "mentionType": 1,  # 1 for user mention, 2 for team mention
    "text": "Kumar Kirtiman"  # Replace with the name of the user or team you want to mention
}

# Message to send as an adaptive card
message = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": "Mention Example",
    "sections": [
        {
            "activityTitle": "Hello from Python!",
            "activitySubtitle": "This is a mention example",
            "activityImage": "",
            "facts": [],
            "markdown": True
        }
    ],
    "potentialAction": [mention]
}

# Send the message using a POST request
try:
    response = requests.post(
        webhook_url,
        json=message,
        headers={"Content-Type": "application/json"}  # Set the Content-Type header
    )

    # Check if the request was successful
    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"An error occurred: {e}")
