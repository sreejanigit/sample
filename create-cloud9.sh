#!/bin/bash

source ./helper.sh

aws iam create-role --path / \
--role-name lattice-workshop-role \
--description "Role used by VPC Lattice Cloud9 environment" \
--assume-role-policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":[\"ec2.amazonaws.com\"]},\"Action\":[\"sts:AssumeRole\"]}]}"

aws iam attach-role-policy --role-name lattice-workshop-role --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

aws iam create-instance-profile --instance-profile-name lattice-workshop-role

aws iam add-role-to-instance-profile --instance-profile-name lattice-workshop-role --role-name lattice-workshop-role

aws cloud9 create-environment-ec2 --name LatticeCloud9 --description "LatticeCloud9 Environment." --instance-type "${CLOUD9_INSTANCE_TYPE}" --image-id resolve:ssm:/aws/service/cloud9/amis/amazonlinux-1-x86_64 --region $AWS_REGION --automatic-stop-time-minutes 300

C9_IDS=$(aws cloud9 list-environments | jq -r '.environmentIds | join(" ")')
CLOUD9_EC2=$(aws cloud9 describe-environments --environment-ids "${C9_IDS}" | jq -r '.environments[] | select(.name == "LatticeCloud9") | .id')

sleep 60

CLOUD9_EC2_ID=$(aws ec2 describe-instances --region "${AWS_REGION}" --filters "Name=tag:aws:cloud9:environment,Values=${CLOUD9_EC2}" --query "Reservations[*].Instances[*].InstanceId" --output text)

aws ec2 associate-iam-instance-profile --instance-id "${CLOUD9_EC2_ID}" --iam-instance-profile Name=lattice-workshop-role --region "${AWS_REGION}"

aws cloud9 update-environment --environment-id "${CLOUD9_EC2}" --managed-credentials-action DISABLE

# aws cloud9 create-environment-membership --environment-id $CLOUD9_ENV_ID --user-arn arn:aws:iam::$AWS_ACCOUNT_ID_VALUE:root --permissions read-write

log_text "Success" "Cloud9 Environment created successfully..."
