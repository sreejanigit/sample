# Disaster Recovery (DR) Orchestrator

## Description

A multi-region disaster recovery strategy provides customers the ability to continue their business operations in another region should the primary region experiences a region-wide disruption. To carry out a DR, many customers rely on runbooks and often execute the DR steps manually. For products consisting of multiple applications, this process an be time consuming and prone to human errors.

The DR orchestrator is an automated solution which orchestrates disaster recoveries between 2 AWS regions, works for products deployed in a single AWS account or across 2 AWS accounts. In the context of the DR Orchestrator, a "product" is a software deployed in AWS. It consists of 1 or more applications, including 3rd party applications. For example, an online retail site (product) consists of an authentication/registration application, a product catalog application, a shopping cart application, and a payment application, etc. 

The DR Orchestrator breaks a DR lifecycle into 4 different phases and automates each of the phases using manifest files and AWS Step Functions. The 4 DR lifecycle phases are: Instantiate, Activate, Cleanup, and Replicate. 

- Instantiate: Deploy the required infrastructure in the secondary region. 
- Activate: Activate the secondary region and make it the primary. 
- Cleanup: When the old primary region comes back online, delete the resources in this region. 
- Replicate: After the resources are cleaned up in the old primary region, re-establish replication from the primary region to the region. The old primary region is now the secondary region. 

A dashboard is created to monitor the progress and status of the DR activities. If there are multiple products, the dashboard will show the status for all of them. 

The following is an architecture diagram of the DR orchestrator:

<img src="diagrams/product-orchestrator.png" width="1000">

1) A person starts the DR workflow by manually executing the aws-dr-orchestrator-stepfunction-product-orchestrator step function. 
2) A request is sent to the person/group who is in charge of approving/rejecting the request. 
3) The step function gets the product manifest file from S3. The file specifies the applications involved in the product, the order they need to be operated on, and the location of the application manifest files. An application manifest file specifies the resources (e.g. database, load balancer, etc) involved in the application, the order they need to be operated on, and the parameters required for the operation. 
4) The manifest files are converted to JSON format from YAML format if required. 
5) The step function gets the application manifest files from S# and invokes the lifecycle step function (instantiate/activate/cleanup/replicate) on the applications. 
6) A dashboard is created to monitor the operations.  

## Prerequisites

The following are required to deploy the DR Orchestrator:
1) An AWS account to deploy the DR Orchestrator. It is recommended to deploy the orchestrator in a different account from the applications but it can also work if they are deployed in the same account. When deployed in different accounts, the accounts must belong to the same AWS Organization.  
2) The applications are running in the primary region, with another region set up as the standby secondary. These regions will be the primary and secondary regions of the DR orchestrator. 
3) A S3 bucket to store the artifacts such as the cloudformation templates and the manifest files in each region (primary and secondary) of the orchestrator account. 
4) An AWS CLI profile that has permission to upload artifacts to the S3 buckets in the Orchestrator account. 
5) A email for DR approvers who will be receiving the mail to approve the DR requests. 
6) If VPC to VPC connectivity is required between the orchestrator account and the application account(s), then please make sure the connectivity is set up properly. e.g. via VPC peering or a transit gateway.
7) Basic knowledge on AWS Step Functions, CloudFormation, Lambda and CloudWatch. 


## Installation

Follow these steps to deploy the DR orchestrator in the Orchestrator account. In single account setups, the process is the same. 

1) Clone the git repository to your local workstation. 

2) Create a parameter file for each region the DR Orchestrator will be deployed to. Use the provided sample files in the "samples" folder as a reference.

| Parameter | Description |
| ----------- | ----------- |
| ApproversEmail | The email address of the group who can approve the DR operations. AWS recommends using Distribution list instead of individual email ids. |
| OrgId  | AWS Organization ID |
| TargetAccountsAssumeRoleName  | The name of the DR execution role that will be deployed in the application accounts. |
| TemplateStoreS3BucketName | The name of the S3 Bucket which stores the cloudformation templates. |
| LambdaSubnet1 | Todo |
| LambdaSubnet2 | Select a subnet from a VPC which the lambdas will be deployed on for special use cases. This subnet is peered with `OpenSearch private subnet on the target account so that the OSS API can be invoked from the orchestrator account. "DeployCF" module uses this subnet to so access GitHub SAS to be able to clone the repo into a S3 bucket for stack creation. If this feature is not required, choose arbitrary subnet just to get through the deployment. |
| LambdaSGId | Select a security group Id which allows above mentioned special use cases. |
| OrchestratorVersion | This is an arbitrary value to force a redeploy of the lambda functions. Increment the version number to force lambda code changes during CICD. |

3) Run the following script to deploy the DR Orchestrator CloudFormation stack in primary region of the Orchestrator account:
```
cd <Orchestrator_Repo_Dir>
bash scripts/deploy-orchestrator.sh
```

4) Repeat step 3 to deploy the DR Orchestrator in secondary region of the Orchestrator account. 

5) In the orchestrator account and EACH application account, use the CloudFormation template role-templates/TargetAccountsAssumeRole.yaml to deploy a DR execution role. The role can be deployed in either region. Optionally you can deploy this stack across all accounts as a [StackSet](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/what-is-cfnstacksets.html). 

Note: If the Orchestrator stack is deleted and recreated, the execution role stack also has to be deleted and recreated in the application accounts. IAM role loses the trust if the role is deleted and the only way to re-establish the trust is to redeploy the role in the spoke accounts.

Run the same deploy-orchestrator.sh script if you want to update the stack with any changes. If you are only updating the lambda code under the lambda_function folder, be sure to update the OrchestratorVersion paramater value to force a stack update, or the changes won't be picked up. 

## Usage

When a disruption occurs in your primary region, you can failover your applications from the primary region to the secondary region to continue your business operations. Let's say your primary region is us-east-1 and your secondary region is us-west-2. us-east-1 is experiencing an outage and you want to failover your applications to us-west-2. A typical DR workflow will look like this: 

1) Deploy the necesssary infrastructure in us-west-2. For example, deploy the applications and ECS instances.  
2) Failover the applications to us-west-2. For example, promote the secondary database instance to primary and switch DNS.
3) When us-east-1 becomes available again, clean up the infrastructure in that region. For example, delete the old database instance, applications and ECS instances. 
4) Re-establish replication between the 2 regions. For example, create a read replica instance in the us-east-1 region. 

This workflow is carried out by the product orchestrator step function, aws-dr-orchestrator-stepfunction-product-orchestrator, with a set of manifest files as the input, as illustrated below. 

<img src="diagrams/dr-lifecycle.png" width="700">

### Example Runbook

The following is an example runbook carrying out the DR process described in the above scenario.

Prerequisites:
All the required manifest files are uploaded to a S3 bucket in both regions. More on manifests below. For example, the following are the paths to the uploaded manifests:

Manifests for the instantiate phase:
- dr-orchestration-artifacts/manifest-files/product-manifest-sampleproduct-INSTANTIATE.json
- dr-orchestration-artifacts/manifest-files/sampleproduct-app1-INSTANTIATE.json
- dr-orchestration-artifacts/manifest-files/sampleproduct-app2-INSTANTIATE.json

Manifests for the activate phase:
- dr-orchestration-artifacts/manifest-files/product-manifest-sampleproduct-ACTIVATE.json
- dr-orchestration-artifacts/manifest-files/sampleproduct-app1-ACTIVATE.json
- dr-orchestration-artifacts/manifest-files/sampleproduct-app2-ACTIVATE.json

Manifests for the cleanup phase:
- dr-orchestration-artifacts/manifest-files/product-manifest-sampleproduct-CLEANUP.json
- dr-orchestration-artifacts/manifest-files/sampleproduct-app1-CLEANUP.json
- dr-orchestration-artifacts/manifest-files/sampleproduct-app2-CLEANUP.json

Manifests for the replicate phase:
- dr-orchestration-artifacts/manifest-files/product-manifest-sampleproduct-REPLICATE.json
- dr-orchestration-artifacts/manifest-files/sampleproduct-app1-REPLICATE.json
- dr-orchestration-artifacts/manifest-files/sampleproduct-app2-REPLICATE.json

#### Step 1: Instantiate the infrastructure in the secondary region us-west-2

1) Login to the AWS console and switch region to us-west-2. You can do it via the AWS CLI as well. Start a new execution on the aws-dr-orchestrator-stepfunction-product-orchestrator step function. Provide the path to the INSTANTIATE product manifest as the input:
```
{
    "productmanifestpath": "dr-orchestration-artifacts/manifest-files/product-manifest-sampleproduct-INSTANTIATE.json"
}
```
Be sure to start the execution of the step function in the correct region.**Starting an execution of Step Function in the wrong region will cause severe disruption including data loss.**

2) An approval email will be sent to the subscribed approvers. Once one of the approvers approved the request, the step function will continue.

#### Step 2: Activate the secondary region us-west-2 as the primary

Once the infrastructure has been successfully instantiated in us-west-2, activate the region to be the primary by failing over the applications to us-west-2. 

1) Login to the AWS console and switch region to us-west-2. You can do it via the AWS CLI as well. Start a new execution on the aws-dr-orchestrator-stepfunction-product-orchestrator step function. Provide the path to the ACTIVATE product manifest as the input:
```
{
    "productmanifestpath": "dr-orchestration-artifacts/manifest-files/product-manifest-sampleproduct-ACTIVATE.json"
}
```

2) An approval email will be sent to the subscribed approvers. Once one of the approvers approved the request, the step function will continue.

#### Step 3: Clean up the resources in the old primary region us-east-1 when it becomes available

When the old primary region us-east-1 becomes available again, clean up the resources that are no longer required/active. 

1) Login to the AWS console and switch region to us-east-1. You can do it via the AWS CLI as well. Start a new execution on the aws-dr-orchestrator-stepfunction-product-orchestrator step function. Provide the path to the ACTIVATE product manifest as the input:
```
{
    "productmanifestpath": "dr-orchestration-artifacts/manifest-files/product-manifest-sampleproduct-CLEANUP.json"
}
```

2) An approval email will be sent to the subscribed approvers. Once one of the approvers approved the request, the step function will continue.

#### Step 4: Re-establish replication between us-west-2 (Primary) and us-east-1 (Secondary)

1) Login to the AWS console and switch region to us-west-2. You can do it via the AWS CLI as well. Start a new execution on the aws-dr-orchestrator-stepfunction-product-orchestrator step function. Provide the path to the ACTIVATE product manifest as the input:
```
{
    "productmanifestpath": "dr-orchestration-artifacts/manifest-files/product-manifest-sampleproduct-REPLICATE.json"
}
```

2) An approval email will be sent to the subscribed approvers. Once one of the approvers approved the request, the step function will continue.

### Product Manifest
We need to be able to swing over a product to another region and product may
consists of several applications and services. The product orchestrator step function is built to
perform the product swings. In order for the product orchestrator to perform the swing a product
manifest is required. The manifest drives the orchestrator to execute the application manifests
in parallel or sequence based on the layers and service order files specified. For each product, there are 4 product manifests: Instantiate manifest, Activate manifest, Cleanup manifest and Replicate manifest. 

Product manifests must be uploaded to the S3 bucket in the orchestrator account. They can be placed in any folder.
 
Here is the schema for the product manifest:

```
{
  "action": "INSTANTIATE | ACTIVATE | REPLICATE | CLEANUP",
  "product_name": "<Name of the product>",
  "product" : [
    {
      "app_layer": 1,
      "apps": [
        {
          "name": "<Application Name>",
          "service_order_files": 
            [
                <Path to application manifest 1>,
                <Path to application manifest 2>
            ]
        }
      ]
    },
    {
      "app_layer": 2,
       ....
    }
  ]
}
```

Order of execution:
1.	app_layer: Executes in a sequence.
2.	apps: Executes in parallel
3.	service_order_files: Executes in parallel.

| Key | Type | Description |
| ----------- | ----------- | ----------- |
| action | String | The DR lifecycle action to invoke. Allowed values are: INSTANTIATE, ACTIVATE, REPLICATE and CLEANUP. |
| product_name | String | Name of the product. It can contain only alphanumeric characters (case-sensitive) and hyphens. It must start with an alphabetic character and can't be longer than 128 characters. |
| product | Array of dictionaries | This array definition makes up the product |
| app_layer | Number | Specifies the sequence of the layer. Please note, this field is only to improve the readability but the orchestrator processes the app array as ordered list. The order in which it is defined is honored and not the number specified. |
| apps | Dictionary | It has 2 keys, Name and apps |
| name | String | Name of the application. It can contain only alphanumeric characters (case-sensitive) and hyphens. It must start with an alphabetic character and can't be longer than 128 characters. Example:
"name": "Foundational-enablement-apps" |
| service_order_files | Array of String | Path to the application manifests in s3 bucket without the bucket name as prefix. |

A naming convention for the product manifest is key because when an email is sent out for an approval, this is the only piece of information that the approver will see on the email to approve or deny. Use  "Product-manifest-\<ProductName>-\<LifecycleAction>.json". Please refer to a sample product manifest file in the "example" folder. 

### Application Manifest

Every application within a product is comprised of set of resources that has to be brought up in a specific order for the service in the application to be available. This is also to address any dependencies it may have. For example, a database may need to be brought up before the app service is started and the DNS is switched over to point to ALB to start accepting traffic. The order in this scenario is: first the database, second the app service and then the DNS change. This order is specified in the application manifest. The application could be a 3rd party application as well as an AWS application. 

For each application, there are 4 manifests, one for each lifecycle stages: Instantiate,
Activate, Replication and cleanup

Similar to product manifests, application manifest must be uploaded to the S3 bucket in the orchestrator account. They can be placed in any folder. 

Here is the schema for the application manifest:

```
[
    {
        "layer": 1,
        "resources": [
            {
                "resourceType": "<resource type 1>",
                "resourceName": "<resource name 1>",
                "parameters": {
                    "<parameter1>": "<value1>",
                    "<parameter2>": "<value2>"
                }
            },
            {
                "resourceType": "<resource type 2>",
                ...
            }
        ]
    },
    {
        "layer": 2,
        ...
    }
]

```
| Key | Type | Description |
| ----------- | ----------- | ----------- |
| layer | Number | The sequence of execution. Each layer will be processed in a sequence. Start with resources in layer 1 that does not have any dependency in app stack and in incrementing layers list the resources that have dependencies with the layer above it. i.e, layer 2 is dependent on layer 1 and so on. The layers are processed in the order it is listed. Switching the layer number from 3 to 2 does not switch the order of execution, instead move the block to the appropriate order in the list.|
| resources | Array of dictionaries | If within the layer there are more than one resources that can be processed in parallel, list all of them under resources. The resources are processed in the order it is listed. |
| resourceType | String | A value identifying the operation. These operations are lisetd as ResourceType in step functions aws-dr-orchestrator-stepfunction-INSTANTIATE, aws-dr-orchestrator-stepfunction-ACTIVATE, aws-dr-orchestrator-stepfunction-CLEANUP and aws-dr-orchestrator-stepfunction-REPLICATE. For example, in the ACTIVATE action, the following are valid operations as shown in the ResourceType in the aws-dr-orchestrator-stepfunction-INSTANTIATE step function: DeployCF, JenkinsJob, OpenSearchScaleUp, ModuleTest, InvokeLambda. |
| resourceName | String | Name of the resource, can be an arbitrary value. |
| parameters | Array of dictionaries | Parameters that identifies the resources. Parameters can include references to Cloudformation exports using the special token "!Import" or refer an SSM parameter using special token "resolve:ssm". Please refer to [here](cloudformation/modules/aurora.md) for more information and examples. |

## Troubleshoot Stepfunction Failures
The orchestrator creates a dashboard in the central account to aggregate all the stepfunction failures happens along the way of the orchestrator execution.
To view the dashboard, 
1. login to the central account
2. To region where the execution has started.
3. Go to "CloudWatch"
4. Click on "Dashboards"
5. You will see dashboard with name "<Product>-Troubleshooting-Dashboard"
6. On the dashboard identify and expand on the failed execution which you want to troubleshoot.
<img src="diagrams/troubleshoot-stepfunction-failures.png" width="700">

7. With the above information on the log, we should be able to locate the stepfunction. 
8. Navigate to the stepfunction using the Step Function name in the detail.stateMachineArn
9. Within the stepfunction, search for the execution using the execution id found in the detail.name. 
10. Open up the execution and that will show the failed step and the error messages from
which you should be able to get to lambda logs and troubleshoot further.





