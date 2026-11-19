#!/usr/bin/env bash
# One-time setup: let the existing project owner assume a restricted lab role.
set -euo pipefail

admin_profile="${1:?Usage: ./scripts/bootstrap-operator.sh ADMIN_PROFILE}"
region_name="ap-northeast-2"
role_name="B3_1OperatorRole"
account_id="$(aws sts get-caller-identity --profile "$admin_profile" --query Account --output text)"
caller_arn="$(aws sts get-caller-identity --profile "$admin_profile" --query Arn --output text)"
if [[ "$caller_arn" == *:root ]]; then
  echo 'Do not use root to create the lab role.' >&2
  exit 2
fi
case "$caller_arn" in
  arn:aws:iam::*:user/*)
    owner_role_arn="$caller_arn" ;;
  arn:aws:sts::*:assumed-role/*)
    source_role_name="${caller_arn#*:assumed-role/}"
    source_role_name="${source_role_name%%/*}"
    owner_role_arn="$(aws iam get-role --profile "$admin_profile" \
      --role-name "$source_role_name" --query Role.Arn --output text)" ;;
  *)
    echo "Unsupported IAM identity: $caller_arn" >&2
    exit 2 ;;
esac
if aws iam get-role --profile "$admin_profile" --role-name "$role_name" >/dev/null 2>&1; then
  echo "Role $role_name already exists. Review its trust and permissions before reuse." >&2
  exit 2
fi

trust_file="$(mktemp)"
policy_file="$(mktemp)"
trap 'rm -f "$trust_file" "$policy_file"' EXIT
cat >"$trust_file" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "$owner_role_arn"},
    "Action": "sts:AssumeRole"
  }]
}
EOF
cat >"$policy_file" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ManageOnlyLabCloudFormationInSeoul",
      "Effect": "Allow",
      "Action": [
        "cloudformation:ValidateTemplate",
        "cloudformation:CreateStack",
        "cloudformation:UpdateStack",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:ListStackResources",
        "cloudformation:CreateChangeSet",
        "cloudformation:DescribeChangeSet",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:DeleteChangeSet",
        "cloudformation:GetTemplateSummary"
      ],
      "Resource": "*",
      "Condition": {"StringEquals": {"aws:RequestedRegion": "$region_name"}}
    },
    {
      "Sid": "PassOnlyLabExecutionRole",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::$account_id:role/B3_1CloudFormationRole",
      "Condition": {"StringEquals": {"iam:PassedToService": "cloudformation.amazonaws.com"}}
    },
    {
      "Sid": "InspectOnlySeoulEC2Resources",
      "Effect": "Allow",
      "Action": ["ec2:DescribeInstances", "ec2:DescribeVolumes", "ec2:DescribeVpcs", "ec2:DescribeSubnets", "ec2:DescribeRouteTables", "ec2:DescribeSecurityGroups", "ec2:DescribeInternetGateways", "ec2:DescribeAddresses"],
      "Resource": "*",
      "Condition": {"StringEquals": {"aws:RequestedRegion": "$region_name"}}
    }
  ]
}
EOF

aws iam create-role --profile "$admin_profile" --role-name "$role_name" \
  --assume-role-policy-document "file://$trust_file" \
  --tags Key=Project,Value=B3_1 >/dev/null
aws iam put-role-policy --profile "$admin_profile" --role-name "$role_name" \
  --policy-name B3_1OperatorSeoulOnly --policy-document "file://$policy_file"
aws iam get-role --profile "$admin_profile" --role-name "$role_name" \
  --query Role.Arn --output text
