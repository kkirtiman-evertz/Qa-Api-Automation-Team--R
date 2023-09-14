const github = require('@actions/github');
const issueComment = "Thank you for opening this issue!";
const client = new github.GitHub(process.env.GITHUB_TOKEN);
client.issues.createComment({
  issue_number: github.context.payload.issue.number,
  owner: github.context.repo.owner,
  repo: github.context.repo.repo,
  body: issueComment,
});
