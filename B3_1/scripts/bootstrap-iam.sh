#!/usr/bin/env bash
# One-time CloudFormation service-role setup by a trusted account administrator.
set -euo pipefail

profile_name="${1:?Usage: ./scripts/bootstrap-iam.sh ADMIN_PROFILE}"
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
role_name="B3_1CloudFormationRole"

identity_arn="$(aws sts get-caller-identity --profile "$profile_name" --query Arn --output text)"
if [[ "$identity_arn" == *:root ]]; then
  echo 'Use a non-root administrator identity to create the lab role.' >&2
  exit 2
fi

if ! aws cloudformation validate-template --profile "$profile_name" --region ap-southeast-2 \
  --template-body "file://$project_dir/infrastructure/cloudformation.yaml" >/dev/null; then
  echo 'Sydney-region template validation failed. No IAM role was created.' >&2
  exit 1
fi

if aws iam get-role --profile "$profile_name" --role-name "$role_name" >/dev/null 2>&1; then
  echo "Role $role_name already exists. Review its trust and permissions before reuse." >&2
  exit 2
fi

aws iam create-role \
  --profile "$profile_name" --role-name "$role_name" \
  --assume-role-policy-document "file://$project_dir/infrastructure/iam/cloudformation-trust.json" \
  --tags Key=Project,Value=B3_1 >/dev/null
aws iam put-role-policy \
  --profile "$profile_name" --role-name "$role_name" \
  --policy-name B3_1EC2VPCSydneyOnly \
  --policy-document "file://$project_dir/infrastructure/iam/cloudformation-permissions.json"

aws iam get-role --profile "$profile_name" --role-name "$role_name" \
  --query 'Role.Arn' --output text
echo 'The role is ready for policy review. IAM changes may take a short time to propagate.'
