#!/usr/bin/env bash
# Delete the lab stack after evidence collection; then audit the checklist.
set -euo pipefail

profile_name="${1:?Usage: ./scripts/cleanup.sh PROFILE}"
region_name="ap-northeast-2"
stack_name="b3-1"

identity_arn="$(aws sts get-caller-identity --profile "$profile_name" --query Arn --output text)"
if [[ "$identity_arn" == *:root ]]; then
  echo 'Do not clean up with the AWS root account. Use the lab IAM identity.' >&2
  exit 2
fi

echo "Deleting $stack_name in $region_name as $identity_arn"
aws cloudformation delete-stack --profile "$profile_name" --region "$region_name" --stack-name "$stack_name"
aws cloudformation wait stack-delete-complete --profile "$profile_name" --region "$region_name" --stack-name "$stack_name"
echo 'CloudFormation stack deleted. Verify EC2, EBS, EIP, IGW and VPC in docs/cleanup-checklist.md.'
