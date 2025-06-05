# Summary of Changes

## Issue Fixed

The following error was fixed:
```
2025-06-05 15:56:47,353 - tokugawa_bot - ERROR - Failed to set up CloudWatch logging: An error occurred (AccessDeniedException) when calling the CreateLogGroup operation: User: arn:aws:sts::959903454321:assumed-role/S3AccessRoleForTokugawa/2a10d5786ae4496a94d2cde601b41381 is not authorized to perform: logs:CreateLogGroup on resource: arn:aws:logs:us-east-1:959903454321:log-group:/ecs/tokugawa-bot:log-stream: because no identity-based policy allows the logs:CreateLogGroup action
```

## Changes Made

1. **Updated IAM Policy**:
   - Modified `s3-access-policy.json` to include CloudWatch logs permissions
   - Added the following permissions:
     - `logs:CreateLogGroup`
     - `logs:CreateLogStream`
     - `logs:PutLogEvents`
   - These permissions allow the bot to create and write to CloudWatch logs

## Why This Fixes the Issue

The error occurred because the IAM role `S3AccessRoleForTokugawa` did not have permission to create a CloudWatch log group. The bot attempts to set up CloudWatch logging when running in AWS (as detected by the presence of the `AWS_EXECUTION_ENV` environment variable).

In the `bot.py` file, the code tries to create a CloudWatch log group named `/ecs/tokugawa-bot` and a log stream named `discord-bot-logs`. However, the IAM role only had permissions for S3 operations, not CloudWatch logs operations.

By adding the necessary CloudWatch logs permissions to the IAM policy, the bot will now be able to create the log group and stream, and write logs to CloudWatch.

## Implementation Details

The CloudWatch logging setup in `bot.py` (lines 14-39) remains unchanged. The only change was to the IAM policy to grant the necessary permissions.

## Deployment Instructions

After committing these changes, the updated IAM policy needs to be applied to the `S3AccessRoleForTokugawa` role in AWS. This can be done using the AWS CLI or the AWS Management Console:

```bash
aws iam put-role-policy \
  --role-name S3AccessRoleForTokugawa \
  --policy-name S3AccessPolicy \
  --policy-document file://s3-access-policy.json
```

## Testing

Once the updated policy is applied, the bot should be able to create CloudWatch log groups and streams, and the error should no longer occur. The logs will be available in the CloudWatch console under the log group `/ecs/tokugawa-bot`.