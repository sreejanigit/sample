from .module import Module
from .utils.boto3_session import Boto3Session
import os
import inspect
import sys
from .utils.logger import Logger
import botocore
from datetime import datetime


class EcsService(Module):

    boto3_service_name = 'ecs'

    def get_scalable_targets(self, cluster_name, service_name, account_id):
        try:
            self.logger.info(
                f"Getting Scalable Targets for Cluster: {cluster_name}, Service: {service_name}")
            application_autoscaling = Boto3Session(self.logger, account_id=account_id,
                                                   service_name='application-autoscaling', region=os.environ["AWS_REGION"]).get_client()
            response = application_autoscaling.describe_scalable_targets(
                ServiceNamespace='ecs',
                ResourceIds=[
                    'service/'+cluster_name+'/'+service_name,
                ]
            )
            self.logger.debug(response)

            return response['ScalableTargets']
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def set_scalable_target_size(self, target_data, desired_count, account_id):
        try:
            self.logger.info(
                f"Setting scalable target size min to {desired_count}")
            application_autoscaling = Boto3Session(self.logger, account_id=account_id,
                                                   service_name='application-autoscaling', region=os.environ["AWS_REGION"]).get_client()
            resource_id = target_data[0]['ResourceId']
            response = application_autoscaling.register_scalable_target(
                ServiceNamespace='ecs',
                ResourceId=target_data[0]['ResourceId'],
                ScalableDimension='ecs:service:DesiredCount',
                MinCapacity=desired_count,
                MaxCapacity=target_data[0]['MaxCapacity']
            )
            self.logger.debug(response)
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def set_replica_size(self, cluster_name, service_name, size, account_id, **kwargs):
        try:
            cluster_desired_count = self.check_task_count(
                self, cluster_name, service_name)
            scalable_targets = self.get_scalable_targets(
                self, cluster_name, service_name, account_id)

            if len(scalable_targets) > 0:
                if kwargs['min_size'] != None:
                    self.set_scalable_target_size(self,
                                                  scalable_targets, int(kwargs['min_size']), account_id)

            if cluster_desired_count == size:
                self.logger.info(f"Task count is already {size}")
                return
            response = self.service_client.update_service(
                cluster=cluster_name,
                service=service_name,
                desiredCount=size
            )
            self.logger.info(response)
            return response
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def check_task_count(self, cluster_name, service_name):
        try:
            response = self.service_client.describe_services(
                cluster=cluster_name,
                services=[
                    service_name,
                ]
            )
            print(response)

            if len(response["failures"]) > 0:
                raise Exception(response["failures"])
            else:
                return response["services"][0]["runningCount"]
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    ### active ###
    def activate(self, event):
        raise Exception(
            "Active is not applicable to EcsService capability")

    def activate_status_check(self, event):
        raise Exception(
            "Active is not applicable to EcsService capability")

    ### instantiate ###
    @Module.init
    def instantiate(self, event):
        module_parameters = event['StatePayload']['parameters']
        account_id = event['StatePayload']['AccountId']
        if isinstance(module_parameters, list):
            for param in module_parameters:
                self.logger.info(f"Instantiate the resource {param}")
                self.set_replica_size(self,
                                      cluster_name=param['EcsClusterName'],
                                      service_name=param['EcsServiceName'],
                                      size=int(param['EcsDesiredSize']),
                                      account_id=account_id,
                                      min_size=param.get('EcsAsgMinSize', None))
        else:
            raise Exception(
                "ECS Service module expects the parameters to be list of dicts")

    @Module.init
    def instantiate_status_check(self, event):
        module_parameters = event['StatePayload']['parameters']
        status_tracker = []
        if isinstance(module_parameters, list):
            for param in module_parameters:
                self.logger.info(
                    f"Instantiate statis for the resource {param}")
                task_count = self.check_task_count(self,
                                                   cluster_name=param['EcsClusterName'],
                                                   service_name=param['EcsServiceName'])
                self.logger.info(f"Running Task Count: {task_count}")

                if task_count == int(param['EcsDesiredSize']):
                    status_tracker.append(True)
                else:
                    status_tracker.append(False)
        else:
            raise Exception(
                "ECS Service module expects the parameters to be list of dicts")
        return all(status_tracker)

    ### replicate ###
    def replicate(self, event):
        raise Exception(
            "Replicate is not applicable to EcsService capability")

    def replicate_status_check(self, event):
        raise Exception(
            "Replicate is not applicable to EcsService capability")

    ### cleanup ###
    @Module.init
    def cleanup(self, event):
        module_parameters = event['StatePayload']['parameters']
        account_id = event['StatePayload']['AccountId']
        if isinstance(module_parameters, list):
            for param in module_parameters:
                self.logger.info(f"Cleanupthe resource {param}")
                self.set_replica_size(self,
                                      cluster_name=param['EcsClusterName'],
                                      service_name=param['EcsServiceName'],
                                      size=0,
                                      account_id=account_id,
                                      min_size=0)
        else:
            raise Exception(
                "ECS Service module expects the parameters to be list of dicts")

    @Module.init
    def cleanup_status_check(self, event):
        module_parameters = event['StatePayload']['parameters']
        status_tracker = []
        if isinstance(module_parameters, list):
            for param in module_parameters:
                self.logger.info(f"Activate statis for the resource {param}")
                task_count = self.check_task_count(self,
                                                   cluster_name=param['EcsClusterName'],
                                                   service_name=param['EcsServiceName'])
                self.logger.info(f"Running Task Count: {task_count}")

                if task_count == 0:
                    status_tracker.append(True)
                else:
                    status_tracker.append(False)
        else:
            raise Exception(
                "ECS Service module expects the parameters to be list of dicts")

        return all(status_tracker)
