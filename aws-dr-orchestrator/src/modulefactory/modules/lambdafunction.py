from .module import Module
from .utils.boto3_session import Boto3Session
import os
import inspect
import sys
from .utils.logger import Logger
import botocore
import json

class LambdaFunction(Module):

    boto3_service_name = 'lambda'

    ### Custom functions ###
    
    def trigger_lambda(self, event):
        
        function_name = event['StatePayload']['parameters']['FunctionName']
        payload = event['StatePayload']['parameters'].get("Payload", {})
        
        response = self.service_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            LogType='Tail',
            Payload=json.dumps(payload)
        )
        
        self.logger.info(response)
        
    ### Lifecycle functions ###

    ### instantiate ###
    @Module.init
    def instantiate(self, event):
        self.trigger_lambda(self, event)

    def instantiate_status_check(self, event):
        return True

    ### activate ###
    @Module.init
    def activate(self, event):
        self.trigger_lambda(self, event)


    def activate_status_check(self, event):
        return True

    ### replicate ###
    @Module.init
    def replicate(self, event):
        self.trigger_lambda(self, event)

    def replicate_status_check(self, event):
        return True

    ### cleanup ###
    @Module.init
    def cleanup(self, event):
        self.trigger_lambda(self, event)

    def cleanup_status_check(self, event):
        return 
