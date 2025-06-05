# Git Commit Best Practices

## Why Meaningful Commits Matter

Meaningful git commits are essential for several reasons:

1. **Historical Context**: They provide a clear history of changes, making it easier to understand why certain decisions were made.
2. **Debugging**: When issues arise, well-documented commits help identify when and why problems were introduced.
3. **Code Reviews**: Clear commit messages make code reviews more efficient by explaining the purpose of changes.
4. **Collaboration**: They help team members understand each other's work without extensive communication.
5. **Rollbacks**: If a change needs to be reverted, meaningful commits make it easier to identify what needs to be undone.

## Best Practices for Git Commits

1. **Write a concise subject line**:
   - Keep it under 50 characters
   - Use the imperative mood (e.g., "Fix bug" not "Fixed bug")
   - Capitalize the first letter
   - Don't end with a period

2. **Provide a detailed body**:
   - Separate from the subject with a blank line
   - Explain what and why, not how
   - Use bullet points for multiple changes
   - Wrap lines at 72 characters

3. **Reference issues and tickets**:
   - Include references to relevant issues or tickets
   - Use keywords like "Fixes", "Resolves", or "Closes" to automatically close issues

4. **Keep commits focused**:
   - Each commit should represent a single logical change
   - Don't mix unrelated changes in the same commit
   - Make frequent, smaller commits rather than large, infrequent ones

5. **Use conventional commit format**:
   - Type: feat, fix, docs, style, refactor, test, chore
   - Scope: optional section indicating what part of the codebase is affected
   - Example: `fix(auth): prevent timing attack in password verification`

## Examples of Good Commit Messages

```
fix(aws): Add CloudWatch logs permissions to IAM policy

Updated s3-access-policy.json to include permissions for CloudWatch logs operations:
- logs:CreateLogGroup
- logs:CreateLogStream
- logs:PutLogEvents

This allows the bot to create log groups and streams, and to put log events into
CloudWatch logs when running in AWS.

Error fixed: "Failed to set up CloudWatch logging: An error occurred (AccessDeniedException)"
```

```
feat(ui): Add dark mode toggle to user settings

- Added toggle switch component to user settings page
- Implemented theme switching logic in ThemeProvider
- Added local storage persistence for theme preference
- Updated tests to cover new functionality

Closes #123
```