#!/bin/bash

source ./helper.sh

set +e

C9_IDS=$(aws cloud9 list-environments | jq -r '.environmentIds | join(" ")')
CLOUD9_EC2=$(aws cloud9 describe-environments --environment-ids "${C9_IDS}" | jq -r '.environments[] | select(.name == "LatticeCloud9") | .id')

aws cloud9 delete-environment --environment-id "${CLOUD9_EC2}"

sleep 120

aws iam remove-role-from-instance-profile --instance-profile-name lattice-workshop-role --role-name lattice-workshop-role

aws iam delete-instance-profile --instance-profile-name lattice-workshop-role

aws iam list-attached-role-policies --role-name lattice-workshop-role | \
jq -r '.AttachedPolicies[].PolicyArn' | \
xargs -I {} aws iam detach-role-policy --policy-arn {} --role-name lattice-workshop-role

aws iam delete-role --role-name lattice-workshop-role

aws iam delete-policy --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/${LATTICE_POLICY}

log_text "Success" "Cleanup successfully..."
