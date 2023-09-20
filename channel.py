import requests
import json

# Define the message content for your comment
comment_content = "This is a comment for the channel."

def send_comment_to_channel(channel_id, comment_text):
    # Define the message payload
    message_payload = {
        "body": {
            "content": comment_text
        }
    }

    # Define the URL for posting the message to the channel
    url = f"https://graph.microsoft.com/v1.0/teams/{your-team-id}/channels/{channel_id}/messages"
    
    # Define your access token (you need to obtain this via authentication)
    access_token = "your-access-token"

    # Set up the headers with the access token and content type
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Send the message to the channel using the Microsoft Graph API
    response = requests.post(url, data=json.dumps(message_payload), headers=headers)

    if response.status_code == 201:
        print("Comment posted successfully.")
    else:
        print("Failed to post comment.")

# Call the function to send a comment to the channel
# Replace 'your-channel-id' with the actual channel ID and provide your comment text
channel_id = "19%3a7aca7755587a42a995e838b64712ca7f%40thread.tacv2"
send_comment_to_channel(channel_id, comment_content)
