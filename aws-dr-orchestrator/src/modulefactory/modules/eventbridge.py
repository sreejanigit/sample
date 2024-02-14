from .module import Module
from .utils.boto3_session import Boto3Session
import os
import inspect
import sys
from .utils.logger import Logger
import botocore


class EventBridge(Module):

    boto3_service_name = 'events'

    ### Custom functions ###
    def enable_event(self, event_name, event_bus):
        try:
            # Check if the rule is already enabled
            status = self.describe_event(self, event_name, event_bus)
            if status == "ENABLED":
                self.logger.info(f"Event {event_name} is already enabled")
                return
            # Enable the rule
            response = self.service_client.enable_rule(
                Name=event_name,
                EventBusName=event_bus
            )
            self.logger.info(response)
            return response
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def disable_event(self, event_name, event_bus):
        try:
            status = self.describe_event(self, event_name, event_bus)
            if status == "DISABLED":
                self.logger.info(f"Event {event_name} is already disabled")
                return
            response = self.service_client.disable_rule(
                Name=event_name,
                EventBusName=event_bus
            )
            return response
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def describe_event(self, event_name, event_bus):
        try:
            response = self.service_client.describe_rule(
                Name=event_name,
                EventBusName=event_bus
            )
            return response["State"]
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    ### Lifecycle functions ###

    ### instantiate ###
    def instantiate(self, event):
        raise Exception(
            "Instantiate is not applicable to EventBridge capability")

    def instantiate_status_check(self, event):
        raise Exception(
            "Instantiate is not applicable to EventBridge capability")

    ### activate ###
    @Module.init
    def activate(self, event):
        module_parameters = event['StatePayload']['parameters']
        for param in module_parameters:
            self.logger.info(f"Activating the resource {param}")
            self.enable_event(self,
                              event_name=param['EventRuleName'],
                              event_bus=param['BusName']
                              )

    @Module.init
    def activate_status_check(self, event):
        all_status = []
        module_parameters = event['StatePayload']['parameters']
        for param in module_parameters:
            status = self.describe_event(self,
                                         event_name=param['EventRuleName'],
                                         event_bus=param['BusName']
                                         )
            self.logger.info(f"status: {status}")
            if status == "ENABLED":
                all_status.append(True)
            elif status == "DISABLED":
                all_status.append(False)
            else:
                return Exception("Rule did not transition to ENABLED state. Please verify.")

        return all(all_status)

    ### replicate ###
    def replicate(self, event):
        raise Exception(
            "Replicate is not applicable to EventBridge capability")

    def replicate_status_check(self, event):
        raise Exception(
            "Replicate is not applicable to EventBridge capability")

    ### cleanup ###
    @Module.init
    def cleanup(self, event):
        module_parameters = event['StatePayload']['parameters']
        for param in module_parameters:
            self.disable_event(self,
                               event_name=param['EventRuleName'],
                               event_bus=param['BusName']
                               )

    @Module.init
    def cleanup_status_check(self, event):
        all_status = []
        module_parameters = event['StatePayload']['parameters']
        for param in module_parameters:
            status = self.describe_event(self,
                                         event_name=param['EventRuleName'],
                                         event_bus=param['BusName'])
            if status == "DISABLED":
                all_status.append(True)
            elif status == "ENABLED":
                all_status.append(False)
            else:
                return Exception("Rule did not transition to DISABLED state. Please verify.")

        return all(all_status)
