from .module import Module
from .utils.boto3_session import Boto3Session
import os
import inspect
import sys
import botocore


# ConcreteProductA
class AutoScaling(Module):
    boto3_service_name = "autoscaling"
    
    def get_autoscaling_groups_instantaite(self, asg_names, desired_count):
        try:
            desiredsize_updated = []
            for asg_name in asg_names:
                response = self.service_client.describe_auto_scaling_groups(
                            AutoScalingGroupNames = [
                                asg_name
                                ])
                desiredsize_updated.append(response['AutoScalingGroups'][0]['DesiredCapacity'])
            for desired_size in desiredsize_updated :
                if (desiredsize_updated[desired_size] == desired_count and desiredsize_updated[desired_size] == desired_count):
                    return {
                            'status': "complete"
                            
                          }
                
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise        
        
    def get_autoscaling_groups_cleanup(self, asg_names):
        try:
            desiredsize_updated = []
            for asg_name in asg_names:
                response = self.service_client.describe_auto_scaling_groups(
                            AutoScalingGroupNames = [
                                asg_name
                                ])
                desiredsize_updated.append(response['AutoScalingGroups'][0]['DesiredCapacity'])
            for desired_size in desiredsize_updated :
                if (desiredsize_updated[desired_size] == 0 and desiredsize_updated[desired_size] == 0):
                    return {
                            'status': "complete"
                            
                          }
                
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise      
        
    def increase_autoscaling_group(self, asg_names, desired_count):
        
        try:
            
            for asg_name in asg_names:
                    response1 = self.service_client.update_auto_scaling_group(
                    AutoScalingGroupName=asg_name,
                    DesiredCapacity=desired_count
                    )
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
        
    def reduce_autoscaling_group(self, asg_names):
        try:
            for asg_name in asg_names:
                response1 = self.service_client.update_auto_scaling_group(
                AutoScalingGroupName=asg_name,
                DesiredCapacity=0
                )
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    @Module.init
    def instantiate(self, event, boto3_service_name=boto3_service_name):
        account_id = event['StatePayload']['parameters']['AccountId']
        asg_names = event['StatePayload']['parameters']['Autoscalinggroupnames']
        desired_count = int(event['StatePayload']['parameters']['DesiredCount'])
        self.increase_autoscaling_group(self, asg_names,desired_count)
        
    @Module.init        
    def instantiate_status_check(self, event, boto3_service_name=boto3_service_name):
        asg_names = event['StatePayload']['parameters']['Autoscalinggroupnames']
        desired_count = int(event['StatePayload']['parameters']['DesiredCount'])
        status = self.get_autoscaling_groups_instantaite(self, asg_names, desired_count)['status']
        
        if (status == "complete"):
            return True
        else:
            return False
            
        
    @Module.init
    def cleanup(self, event, boto3_service_name=boto3_service_name):
        account_id = event['StatePayload']['parameters']['AccountId']
        asg_names = event['StatePayload']['parameters']['Autoscalinggroupnames']
        desired_count = int(event['StatePayload']['parameters']['DesiredCount'])
        self.reduce_autoscaling_group(self, asg_names)
        
    @Module.init
    def cleanup_status_check(self, event, boto3_service_name=boto3_service_name):
        asg_names = event['StatePayload']['parameters']['Autoscalinggroupnames']
        desired_count = int(event['StatePayload']['parameters']['DesiredCount'])
        status = self.get_autoscaling_groups_cleanup(self, asg_names)['status']
        
        if (status == "complete"):
            return True
        else:
            return False
        
    @Module.init
    def replicate(self, event, boto3_service_name):
        raise Exception("Instantiate is not applicable to Autoscaling capability")
        
    @Module.init
    def replicate_status_check(self, event, boto3_service_name=boto3_service_name):
        raise Exception("Instantiate is not applicable to Autoscaling capability")
        
    @Module.init
    def activate(self, event):
        raise Exception("Instantiate is not applicable to Autoscaling capability")
    
    @Module.init        
    def activate_status_check(self, event):
        raise Exception("Instantiate status check is not applicable to Autoscaling capability") 
        
    
