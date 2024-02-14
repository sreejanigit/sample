from .module import Module
from .utils.boto3_session import Boto3Session
import os
import inspect
import sys
from .utils.logger import Logger
import botocore
from datetime import datetime


class R53Record(Module):

    boto3_service_name = 'route53'

    def get_canonical_hz_id(self, value, account_id):
        try:
            elb_client = Boto3Session(self.logger, account_id=account_id,
                                      service_name='elbv2', region=os.environ["AWS_REGION"]).get_client()
            response = elb_client.describe_load_balancers(
                Names=[value]
            )
            return response['LoadBalancers'][0]['CanonicalHostedZoneId']
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def get_elb_dnsname(self, value, account_id):
        try:
            elb_client = Boto3Session(self.logger, account_id=account_id,
                                      service_name='elbv2', region=os.environ["AWS_REGION"]).get_client()
            response = elb_client.describe_load_balancers(
                Names=[value]
            )
            return response['LoadBalancers'][0]['DNSName']
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def get_ttl(self, hz_id, rec_name, rec_type):
        try:
            response = self.service_client.list_resource_record_sets(
                HostedZoneId=hz_id,
                StartRecordName=rec_name,
                StartRecordType=rec_type,
            )
            return response['ResourceRecordSets'][0]['TTL']
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def update_record(self, hz_id, rec_name, rec_type, alias_flag, value, account_id):
        try:
            if rec_type == "A":
                if alias_flag == "Yes":
                    ResourceRecords = {
                        'Name': rec_name,
                        'Type': rec_type,
                        'AliasTarget': {
                            'HostedZoneId': self.get_canonical_hz_id(self, value, account_id),
                            'DNSName': self.get_elb_dnsname(self, value, account_id),
                            'EvaluateTargetHealth': False
                        }
                    }
                else:
                    if isinstance(value, list):
                        ResourceRecords = {
                            'Name': rec_name,
                            'Type': rec_type,
                            'TTL': self.get_ttl(self, hz_id, rec_name, rec_type),
                            'ResourceRecords': [{'Value': v} for v in value]
                        }
                    else:
                        ResourceRecords = {
                            'Name': rec_name,
                            'Type': rec_type,
                            'ResourceRecords': [{'Value': value}]
                        }
            elif rec_type == "CNAME":
                if isinstance(value, list):
                    raise Exception(
                        "CNAME record type doesn't accept list of value")
                else:
                    ResourceRecords = {
                        'Name': rec_name,
                        'Type': rec_type,
                        'TTL': self.get_ttl(self, hz_id, rec_name, rec_type),
                        'ResourceRecords': [{'Value':  value}]
                    }
            self.logger.info("Resource Records data for API call")
            self.logger.info(ResourceRecords)
            response = self.service_client.change_resource_record_sets(
                HostedZoneId=hz_id,
                ChangeBatch={
                    'Comment': "Changing DNS Endpoint",
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': ResourceRecords
                        },
                    ],
                },
            )
            self.logger.info(response)
            return response['ChangeInfo']['Id']
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def change_status(self, change_id):
        try:
            response = self.service_client.get_change(
                Id=change_id,
            )
            self.logger.info(response)
            return response['ChangeInfo']['Status']
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    ### active ###
    @Module.init
    def activate(self, event):
        module_parameters = event['StatePayload']['parameters']
        account_id = event['StatePayload']['AccountId']
        return_data = []
        if isinstance(module_parameters, list):
            for param in module_parameters:
                self.logger.info(f"Activating the Record {param}")
                change_id = self.update_record(self,
                                               hz_id=param['HostedZoneId'],
                                               rec_name=param['R53RecordName'],
                                               rec_type=param['RecordType'],
                                               alias_flag=param['Aias'],
                                               value=param['RecordValue'],
                                               account_id=account_id)
                return_data.append(change_id)
            return {"ChangeIds": return_data}
        else:
            raise Exception(
                "ECS Service module expects the parameters to be list of dicts")

    @Module.init
    def activate_status_check(self, event):
        change_id_list = event['lifecycle_output']['Payload']['ChangeIds']
        for change in change_id_list:
            if self.change_status(self, change) != "INSYNC":
                return False
        return True

    ### instantiate ###
    @Module.init
    def instantiate(self, event):
        raise Exception(
            "Instantiate is not applicable to R53Record capability")

    @Module.init
    def instantiate_status_check(self, event):
        raise Exception(
            "Instantiate is not applicable to R53Record capability")

    ### replicate ###
    def replicate(self, event):
        raise Exception(
            "Replicate is not applicable to R53Record capability")

    def replicate_status_check(self, event):
        raise Exception(
            "Replicate is not applicable to R53Record capability")

    ### cleanup ###
    @Module.init
    def cleanup(self, event):
        raise Exception(
            "Cleanupis not applicable to R53Record capability")

    @Module.init
    def cleanup_status_check(self, event):
        raise Exception(
            "Cleanup is not applicable to R53Record capability")
