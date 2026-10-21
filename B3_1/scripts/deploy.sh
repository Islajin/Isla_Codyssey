#!/usr/bin/env bash
# Deploy the CloudFormation stack and copy the B1_1 portfolio to Nginx.
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
profile_name=""
key_name=""
key_file=""
ssh_cidr=""
role_arn=""
stack_name="b3-1"
region_name="ap-southeast-2"

usage() {
  cat <<'EOF'
Usage: ./scripts/deploy.sh --profile NAME --key-name AWS_KEY_NAME \
  --key-file /path/to/key.pem --ssh-cidr YOUR_PUBLIC_IP/32 --role-arn ARN

Run only after checking this account's EC2 Free Tier eligibility and costs.
The CloudFormation execution role must be limited to this project's EC2/VPC resources.
EOF
}

while (($#)); do
  case "$1" in
    --profile) profile_name="${2:?Missing profile name}"; shift 2 ;;
    --key-name) key_name="${2:?Missing EC2 key name}"; shift 2 ;;
    --key-file) key_file="${2:?Missing private key path}"; shift 2 ;;
    --ssh-cidr) ssh_cidr="${2:?Missing SSH CIDR}"; shift 2 ;;
    --role-arn) role_arn="${2:?Missing CloudFormation role ARN}"; shift 2 ;;
    --help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done

if [[ -z "$profile_name" || -z "$key_name" || -z "$key_file" || -z "$ssh_cidr" || -z "$role_arn" ]]; then
  usage >&2
  exit 2
fi
if [[ ! "$ssh_cidr" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/32$ ]]; then
  echo 'SSH CIDR must be a single IPv4 address ending in /32.' >&2
  exit 2
fi
if [[ ! -f "$key_file" ]]; then
  echo "Private key not found: $key_file" >&2
  exit 2
fi
for program in aws ssh tar curl; do
  command -v "$program" >/dev/null || { echo "Missing command: $program" >&2; exit 2; }
done

identity_arn="$(aws sts get-caller-identity --profile "$profile_name" --query Arn --output text)"
if [[ "$identity_arn" == *:root ]]; then
  echo 'Do not deploy with the AWS root account. Use the lab IAM identity.' >&2
  exit 2
fi
echo "Deploying as $identity_arn in $region_name"

if ! aws cloudformation validate-template --profile "$profile_name" --region "$region_name" \
  --template-body "file://$project_dir/infrastructure/cloudformation.yaml" >/dev/null; then
  echo 'Template validation or Sydney-region access failed. No stack deployment was started.' >&2
  exit 1
fi

aws cloudformation deploy \
  --profile "$profile_name" --region "$region_name" \
  --template-file "$project_dir/infrastructure/cloudformation.yaml" \
  --stack-name "$stack_name" --role-arn "$role_arn" \
  --parameter-overrides "KeyName=$key_name" "SshCidr=$ssh_cidr" \
  --tags Project=B3_1 --no-fail-on-empty-changeset

public_ip="$(aws cloudformation describe-stacks --profile "$profile_name" --region "$region_name" \
  --stack-name "$stack_name" --query 'Stacks[0].Outputs[?OutputKey==`PublicIp`].OutputValue | [0]' --output text)"
if [[ -z "$public_ip" || "$public_ip" == None ]]; then
  echo 'Stack has no public IP output. Inspect CloudFormation events.' >&2
  exit 1
fi

ssh_options=(-i "$key_file" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)
for attempt in {1..30}; do
  if ssh "${ssh_options[@]}" "ec2-user@$public_ip" 'test -d /usr/share/nginx/html' >/dev/null 2>&1; then
    break
  fi
  if ((attempt == 30)); then
    echo 'SSH or Nginx is not ready. Check your IP, key, SG, and /var/log/cloud-init-output.log.' >&2
    exit 1
  fi
  sleep 10
done

tar -C "$project_dir/site" -czf - . | ssh "${ssh_options[@]}" "ec2-user@$public_ip" \
  'sudo tar -C /usr/share/nginx/html -xzf - && sudo systemctl reload nginx'

curl --fail --silent --show-error --retry 10 --retry-delay 3 "http://$public_ip/health" | grep -qx OK
echo "Portfolio: http://$public_ip/"
echo "Health:    http://$public_ip/health (200 OK)"
echo 'Run ./scripts/verify.sh for the full evidence checks and take an external screenshot.'
