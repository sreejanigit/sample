# Setup the DR stacks to enable CICD

1. Deploys a CloudFormation stack called "dr-orchestrator-baseline" from the template in baseline.yaml. This sets up initial baseline resources.

2. Zips up the project files, excluding .git and .DS_Store. Uploads this zip file to an S3 bucket created in the baseline templates.

3. Deploys a CloudFormation stack called "dr-orchestrator-repository" from the template codecommit.yaml. This sets up a CodeCommit repository.

4. Deploys a CloudFormation stack called "dr-orchestrator-build-stages" from the template codebuild.yaml. This sets up CodeBuild build stages.

5. Deploys a CloudFormation stack called "dr-orchestrator-pipeline" from the template pipeline.yaml. This sets up a CodePipeline for CI/CD.

The `src/baseline/setup.sh` automates the deployment of a CodeCommit repository, CodeBuild stages, and a CodePipeline to enable CI/CD for the project. The baseline resources like S3 buckets are also created.


# DR Orchestrator Solution - Baseline Resources

## Overview
This template `src/baseline/baseline.yaml` deploys foundational resources needed to enable CI/CD pipelines and service catalog capabilities using AWS CloudFormation.

## Resources Created
- S3 bucket for artifact storage (encrypted and versioned)
- Dedicated S3 bucket for access logs
- KMS key for encryption
- IAM roles for CodePipeline and CloudFormation
- SSM Parameters to store key resource ARNs/names

## Parameters
- CodePipelineServiceRoleName - Name of the CodePipeline service role
- CloudFormationCodePipelineRoleName - Name of the CloudFormation service role
- Tag1/Tag2/Tag3 - Tags to apply to resources

## Outputs
- ServiceCatalogS3BucketName - Name of the S3 artifact bucket
- ServiceCatalogS3BucketArn - ARN of the S3 artifact bucket
- CreateAMIKmsKeyArn - ARN of the KMS key
- CodePipelineStepsRoleOutput - ARN of the CodePipeline role
- CloudFormationRole - ARN of the CloudFormation role

The SSM parameters store essential resource attributes to share across accounts/regions.

This template is the first step in building CI/CD capabilities for the self service catalog. It handles the baseline items needed