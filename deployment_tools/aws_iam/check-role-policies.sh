#!/bin/bash

# List all policies attached to the role
echo "Checking policies attached to S3AccessRoleForTokugawa..."
aws iam list-attached-role-policies --role-name S3AccessRoleForTokugawa

# Check if the DynamoDB policy is attached
echo -e "\nChecking if DynamoDBAccessForTokugawa policy is attached..."
aws iam list-attached-role-policies \
    --role-name S3AccessRoleForTokugawa \
    --query "AttachedPolicies[?PolicyName=='DynamoDBAccessForTokugawa']" \
    --output text

# Get the policy document to verify its contents
echo -e "\nGetting policy document for DynamoDBAccessForTokugawa..."
aws iam get-policy-version \
    --policy-arn arn:aws:iam::959903454321:policy/DynamoDBAccessForTokugawa \
    --version-id v1 