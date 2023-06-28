#!/bin/bash

source ./utils.sh

export ENVIRONMENT_NAME=""

export LATTICE_POLICY="VPCLatticeControllerIAMPolicy"
export DEFAULT_VPC_FILTER="Name=isDefault,Values=true"

export AWS_PAGER=""

export AWS_REGION="us-west-2"

export LATTICE_DOMAIN_NAME="lattice.io"

export CLOUD9_INSTANCE_TYPE="t3.small"

export CLUSTER1_NAME="c1"
export VPC1_NAME='LatticeWorkshop Clients VPC'
export VPC1_FILTER="Name=tag:Name,Values='$VPC1_NAME'"

export CLUSTER2_NAME="c2"
export VPC2_NAME='LatticeWorkshop Rates VPC'
export VPC2_FILTER="Name=tag:Name,Values='$VPC2_NAME'"

export ASSETS_HOSTNAME="assets-${CLUSTER1_NAME}"
export CART_HOSTNAME="cart-${CLUSTER1_NAME}"
export CATALOG_HOSTNAME="catalog-${CLUSTER1_NAME}"
export CHECKOUT_HOSTNAME="checkout-${CLUSTER2_NAME}"

export ASSETS_FQDN="${ASSETS_HOSTNAME}.${LATTICE_DOMAIN_NAME}"
export CART_FQDN="${CART_HOSTNAME}.${LATTICE_DOMAIN_NAME}"
export CATALOG_FQDN="${CATALOG_HOSTNAME}.${LATTICE_DOMAIN_NAME}"
export CHECKOUT_FQDN="${CHECKOUT_HOSTNAME}.${LATTICE_DOMAIN_NAME}"
