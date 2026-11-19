#!/usr/bin/env python3
"""Verify the live Seoul lab against the assignment and save redacted evidence."""

import json
import subprocess
from pathlib import Path


REGION = "ap-northeast-2"
PROFILE = "b3-learner"
STACK = "b3-1"
ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "docs" / "evidence"


def aws(service: str, operation: str, *args: str) -> dict:
    command = ["aws", service, operation, "--profile", PROFILE, "--region", REGION, *args, "--output", "json"]
    return json.loads(subprocess.check_output(command, text=True))


def save(name: str, value: dict) -> None:
    (EVIDENCE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    identity = aws("sts", "get-caller-identity")
    assert identity["Arn"].endswith(":user/B3_1Learner"), "Deployment identity must be the lab IAM user"

    stack = aws("cloudformation", "describe-stacks", "--stack-name", STACK)["Stacks"][0]
    assert stack["StackStatus"] == "CREATE_COMPLETE"
    outputs = {item["OutputKey"]: item["OutputValue"] for item in stack["Outputs"]}
    resources = aws("cloudformation", "list-stack-resources", "--stack-name", STACK)["StackResourceSummaries"]
    resource_ids = {item["LogicalResourceId"]: item["PhysicalResourceId"] for item in resources}

    vpc = aws("ec2", "describe-vpcs", "--vpc-ids", outputs["VpcId"])["Vpcs"][0]
    subnet = aws("ec2", "describe-subnets", "--subnet-ids", outputs["SubnetId"])["Subnets"][0]
    gateway = aws("ec2", "describe-internet-gateways", "--internet-gateway-ids", resource_ids["InternetGateway"])["InternetGateways"][0]
    table = aws("ec2", "describe-route-tables", "--route-table-ids", outputs["RouteTableId"])["RouteTables"][0]
    group = aws("ec2", "describe-security-groups", "--group-ids", outputs["SecurityGroupId"])["SecurityGroups"][0]
    instance = aws("ec2", "describe-instances", "--instance-ids", outputs["InstanceId"])["Reservations"][0]["Instances"][0]
    root_device = next(item for item in instance["BlockDeviceMappings"] if item["DeviceName"] == instance["RootDeviceName"])
    volume_id = root_device["Ebs"]["VolumeId"]
    volume = aws("ec2", "describe-volumes", "--volume-ids", volume_id)["Volumes"][0]

    assert vpc["CidrBlock"] == "10.0.0.0/16"
    assert subnet["CidrBlock"] == "10.0.1.0/24" and subnet["VpcId"] == outputs["VpcId"]
    assert any(item["VpcId"] == outputs["VpcId"] and item["State"] == "available" for item in gateway["Attachments"])
    assert any(item.get("DestinationCidrBlock") == "0.0.0.0/0" and item.get("GatewayId") == gateway["InternetGatewayId"] and item["State"] == "active" for item in table["Routes"])
    assert any(item.get("SubnetId") == outputs["SubnetId"] for item in table["Associations"])

    ingress = group["IpPermissions"]
    assert len(ingress) == 2, "Only HTTP and SSH ingress are allowed"
    http = next(item for item in ingress if item["FromPort"] == item["ToPort"] == 80 and item["IpProtocol"] == "tcp")
    ssh = next(item for item in ingress if item["FromPort"] == item["ToPort"] == 22 and item["IpProtocol"] == "tcp")
    assert [item["CidrIp"] for item in http["IpRanges"]] == ["0.0.0.0/0"]
    ssh_source = ssh["IpRanges"][0]["CidrIp"]
    expected_source = Path("/Users/yeonjin/.aws/B3_1-ssh-cidr.txt").read_text().strip()
    assert ssh_source == expected_source and ssh_source.endswith("/32")
    assert all(item.get("CidrIp") != "0.0.0.0/0" for item in ssh["IpRanges"])

    assert instance["State"]["Name"] == "running"
    assert instance["InstanceType"] == "t3.micro"
    assert instance["SubnetId"] == outputs["SubnetId"]
    assert instance["PublicIpAddress"] == outputs["PublicIp"]
    assert any(item["GroupId"] == outputs["SecurityGroupId"] for item in instance["SecurityGroups"])
    assert volume["Size"] == 8 and volume["VolumeType"] == "gp3" and volume["Encrypted"] is True
    assert root_device["Ebs"]["DeleteOnTermination"] is True

    network = {
        "region": REGION,
        "stackStatus": stack["StackStatus"],
        "vpcId": outputs["VpcId"],
        "vpcCidr": vpc["CidrBlock"],
        "publicSubnetId": outputs["SubnetId"],
        "publicSubnetCidr": subnet["CidrBlock"],
        "internetGatewayId": gateway["InternetGatewayId"],
        "internetGatewayAttachedToVpc": True,
        "publicRouteTableId": outputs["RouteTableId"],
        "defaultRoute": "0.0.0.0/0 -> " + gateway["InternetGatewayId"],
        "defaultRouteState": "active",
        "routeTableAssociatedWithPublicSubnet": True,
    }
    security = {
        "securityGroupId": outputs["SecurityGroupId"],
        "inboundRules": [
            {"protocol": "tcp", "port": 80, "source": "0.0.0.0/0"},
            {"protocol": "tcp", "port": 22, "source": "learner current IPv4/32 (redacted)", "matchesLocalIp": True},
        ],
        "allPortsOpenToInternet": False,
    }
    compute = {
        "instanceId": outputs["InstanceId"],
        "state": instance["State"]["Name"],
        "instanceType": instance["InstanceType"],
        "publicIp": instance["PublicIpAddress"],
        "subnetId": instance["SubnetId"],
        "securityGroupId": outputs["SecurityGroupId"],
        "rootEbsVolumeId": volume_id,
        "rootEbsGiB": volume["Size"],
        "rootEbsType": volume["VolumeType"],
        "rootEbsEncrypted": volume["Encrypted"],
        "rootEbsDeleteOnTermination": root_device["Ebs"]["DeleteOnTermination"],
    }
    save("network-audit.json", network)
    save("security-audit.json", security)
    save("instance-audit.json", compute)
    print("Live Seoul AWS audit passed: VPC/subnet/IGW/route, SSH/HTTP SG, EC2, encrypted 8 GiB EBS.")


if __name__ == "__main__":
    main()
