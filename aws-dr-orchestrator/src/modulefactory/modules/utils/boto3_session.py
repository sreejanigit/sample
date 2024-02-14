##############################################################################
#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License").           #
#  You may not use this file except in compliance                            #
#  with the License. A copy of the License is located at                     #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  or in the "license" file accompanying this file. This file is             #
#  distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  #
#  KIND, express or implied. See the License for the specific language       #
#  governing permissions  and limitations under the License.                 #
##############################################################################

from os import getenv

# !/bin/python
import boto3
from botocore.config import Config


class Boto3Session:
    #This class initialize boto3 client for a given AWS service name.

    def __init__(self, logger, service_name, account_id, **kwargs):
        """
        Parameters
        ----------
        logger : object
            The logger object
        region : str
            AWS region name. Example: 'us-east-1'
        service_name : str
            AWS service name. Example: 'ec2'
        credentials = dict, optional
            set of temporary AWS security credentials
        """
        self.logger = logger
        self.service_name = service_name
        self.account_id = account_id
        self.credentials = kwargs.get("credentials", None)
        self.region = kwargs.get("region", None)
        self.target_assume_role_name = getenv("target_assume_role")
        self.solution_id = getenv("SOLUTION_ID", "SO0089")
        self.solution_version = getenv("SOLUTION_VERSION", "undefined")
        user_agent = f"AwsSolution/{self.solution_id}/{self.solution_version}"
        self.boto_config = Config(
            user_agent_extra=user_agent,
            retries={"mode": "standard", "max_attempts": 20},
        )

    def get_client(self):
        """Creates a boto3 low-level service client by name.

        Returns: service client, type: Object
        """
        if self.account_id is not None:
            sts = boto3.client('sts')
            stsresponse = sts.assume_role(
              RoleArn=f"arn:aws:iam::{self.account_id}:role/{self.target_assume_role_name}",
              RoleSessionName='aws-dr-orchestrator-session',
              DurationSeconds=900,
            )
            self.credentials = stsresponse["Credentials"]
        else:
            raise

        if self.credentials is None:
            if self.endpoint_url is None:
                return boto3.client(
                    self.service_name, region_name=self.region, config=self.boto_config
                )
            else:
                return boto3.client(
                    self.service_name,
                    region_name=self.region,
                    config=self.boto_config,
                    endpoint_url=self.endpoint_url,
                )
        else:
            if self.region is None:
                return boto3.client(
                    self.service_name,
                    aws_access_key_id=self.credentials.get("AccessKeyId"),
                    aws_secret_access_key=self.credentials.get("SecretAccessKey"),
                    aws_session_token=self.credentials.get("SessionToken"),
                    config=self.boto_config,
                )
            else:
                return boto3.client(
                    self.service_name,
                    region_name=self.region,
                    aws_access_key_id=self.credentials.get("AccessKeyId"),
                    aws_secret_access_key=self.credentials.get("SecretAccessKey"),
                    aws_session_token=self.credentials.get("SessionToken"),
                    config=self.boto_config,
                )
