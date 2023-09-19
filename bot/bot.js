const { BotFrameworkAdapter, MessageFactory } = require('botbuilder');

// Initialize the Bot Framework Adapter and bot
const adapter = new BotFrameworkAdapter({
  appId: process.env.MICROSOFT_APP_ID,
  appPassword: process.env.MICROSOFT_APP_PASSWORD,
});

// Define the bot's message handler
adapter.onTurn(async (turnContext) => {
  // Check if the message is from GitHub Actions and an "issues" event
  if (
    turnContext.activity.channelId === 'github-actions' &&
    turnContext.activity.type === 'message' &&
    turnContext.activity.text.includes('Issue opened')
  ) {
    // Extract relevant information from the GitHub issue event
    const issueTitle = 'Your issue title'; // Replace with the actual issue title
    const issueURL = 'https://github.com/your-repo/issues/1'; // Replace with the actual issue URL

    // Mention the specific team or group in Microsoft Teams
    // You will need to implement logic to determine how to mention them
    const mention = '@team-or-group';

    // Send a message to Microsoft Teams
    await turnContext.sendActivity(
      MessageFactory.text(
        `${mention} New issue opened: [${issueTitle}](${issueURL})`
      )
    );
  }
});

// Start the bot
adapter.processActivity().catch((err) => {
  console.error('Error processing activity:', err);
});

