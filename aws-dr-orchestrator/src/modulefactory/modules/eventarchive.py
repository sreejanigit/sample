from .module import Module
from .utils.boto3_session import Boto3Session
import os
import inspect
import sys
from .utils.logger import Logger
import botocore
from datetime import datetime


class EventArchive(Module):

    boto3_service_name = 'events'

    def get_bus_arn(self, bus_name):
        try:
            return self.service_client.describe_event_bus(Name=bus_name)['Arn']
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
        return

    ### Create replay ###
    def create_replay(self, archive_arn, event_bus, start_time, end_time, name):
        try:
            response = self.service_client.start_replay(
                ReplayName=name,
                Description=f'Replaying the events from {start_time} to {end_time} in UTC',
                EventSourceArn=archive_arn,
                EventStartTime=datetime.strptime(
                    start_time, '%Y-%m-%d %H:%M:%S'),
                EventEndTime=datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S'),
                Destination={'Arn': self.get_bus_arn(self, event_bus)},
            )
            self.logger.info(response)
            return response
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def describe_replay(self, replay_name):
        try:
            response = self.service_client.describe_replay(
                ReplayName=replay_name,
            )
            return response["State"]
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    ### instantiate ###
    def instantiate(self, event):
        raise Exception(
            "Instantiate is not applicable to EventArchive capability")

    def instantiate_status_check(self, event):
        raise Exception(
            "Instantiate is not applicable to EventArchive capability")

    ### activate ###
    @Module.init
    def activate(self, event):
        self.create_replay(self,
                           archive_arn=event['StatePayload']['parameters']['EventArchiveArn'],
                           event_bus=event['StatePayload']['parameters']['BusName'],
                           start_time=event['StatePayload']['parameters']['StartTime'],
                           end_time=event['StatePayload']['parameters']['EndTime'],
                           name=event['StatePayload']['parameters']['ReplayName'])

    @Module.init
    def activate_status_check(self, event):
        status = self.describe_replay(self,
                                      replay_name=event['StatePayload']['parameters']['ReplayName'])
        self.logger.info(f"status: {status}")
        if status == "COMPLETED":
            return True
        elif status in ["STARTING", "RUNNING"]:
            return False
        else:
            raise Exception(f"Replay is in {status} state. Please verify.")

    ### replicate ###
    def replicate(self, event):
        raise Exception(
            "Replicate is not applicable to EventArchive capability")

    def replicate_status_check(self, event):
        raise Exception(
            "Replicate is not applicable to EventArchive capability")

    ### cleanup ###
    @Module.init
    def cleanup(self, event):
        raise Exception("Cleanup is not applicable to EventArchive capability")

    @Module.init
    def cleanup_status_check(self, event):
        raise Exception("Cleanup is not applicable to EventArchive capability")
