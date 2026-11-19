#!/usr/bin/env bash
# Run after deployment. Writes honest command output, not a substitute for a screenshot.
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
profile_name="${1:?Usage: ./scripts/verify.sh PROFILE /path/to/key.pem}"
key_file="${2:?Usage: ./scripts/verify.sh PROFILE /path/to/key.pem}"
region_name="ap-northeast-2"
stack_name="b3-1"
evidence_file="$project_dir/docs/evidence/verification.txt"

public_ip="$(aws cloudformation describe-stacks --profile "$profile_name" --region "$region_name" \
  --stack-name "$stack_name" --query 'Stacks[0].Outputs[?OutputKey==`PublicIp`].OutputValue | [0]' --output text)"
instance_id="$(aws cloudformation describe-stacks --profile "$profile_name" --region "$region_name" \
  --stack-name "$stack_name" --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue | [0]' --output text)"

{
  echo "Verified at: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  echo "Region: $region_name"
  echo "Instance: $instance_id"
  echo "Public URL: http://$public_ip/"
  echo '--- External health check ---'
  curl --fail --silent --show-error --include "http://$public_ip/health"
  echo
  echo '--- EC2 state ---'
  aws ec2 describe-instances --profile "$profile_name" --region "$region_name" \
    --instance-ids "$instance_id" --query 'Reservations[0].Instances[0].State.Name' --output text
  echo '--- Internal HTTP and internet egress ---'
  ssh -i "$key_file" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new \
    "ec2-user@$public_ip" 'curl -fsS -o /dev/null -w "localhost HTTP %{http_code}\n" http://localhost/ && curl -fsS -o /dev/null -w "internet HTTPS %{http_code}\n" https://example.com/'
} | tee "$evidence_file"

echo "Saved $evidence_file"
echo 'Also save a real browser or curl screenshot as docs/evidence/external-access.png.'
