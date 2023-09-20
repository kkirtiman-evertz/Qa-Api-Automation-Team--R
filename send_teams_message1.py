{
    "type": "message",
    "attachments": [
      {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
          "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
          "type": "AdaptiveCard",
          "version": "1.4",
          "body": [
            {
              "type": "TextBlock",
              "id": "MentionTextBlock",
              "text": "Fun with mentions!",
              "weight": "Bolder",
              "size": "Medium"
            },
            {
              "type": "TextBlock",
              "text": "This is user mention. Hi: <at>USER NAME</at>!",
              "size": "Medium"
            },
            {
              "type": "TextBlock",
              "text": "And this mentions tag <at>TAG NAME</at>!",
              "size": "Medium"
            },
            {
              "type": "TextBlock",
              "text": "This is channel mention. Hello: <at>CHANNEL NAME</at>!",
              "size": "Medium"
            }
          ],
          "msteams": {
            "entities": [
              {
                "type": "mention",
                "text": "<at>USER NAME</at>",
                "mentioned": {
                  "id": "8:orgid:USER AAD ID",
                  "name": "USER NAME"
                }
              },
              {
                "type": "mention",
                "text": "<at>TAG NAME</at>",
                "mentioned": {
                  "id": "TAG ID",
                  "name": "TAG NAME"
                }
              },
              {
                "type": "mention",
                "text": "<at>CHANNEL NAME</at>",
                "mentioned": {
                  "id": "CHANNEL ID",
                  "displayName": "CHANNEL NAME",
                  "conversationIdentityType": "channel",
                  "conversationIdentityType@odata.type": "#Microsoft.Teams.GraphSvc.conversationIdentityType"
                }
              }
            ]
          }
        }
      }
    ]
  }
