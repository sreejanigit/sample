from abc import ABC, abstractmethod
from .utils.logger import Logger
from .utils.boto3_session import Boto3Session
from .utils.parser import Parser
import os

# AbstractProduct


class Module(ABC):

    @classmethod
    def call_lifecycle(self, name: str, event: dict):
        if hasattr(self, name) and callable(func := getattr(self, name)):
            return func(self, event=event)

    @classmethod
    def init(self, func):
        def wrapper(self, *args, **kwargs):

            self.logger = Logger()

            account_id = kwargs['event']['StatePayload']['AccountId']
            service_name = self.boto3_service_name

            if account_id and service_name:
                self.logger.debug(f'Creating a session...')
                session = Boto3Session(self.logger, account_id=account_id,
                                       service_name=service_name, region=os.environ["AWS_REGION"])
                self.service_client = session.get_client()

                session = Boto3Session(
                    self.logger, account_id=account_id, service_name='ssm', region=os.environ["AWS_REGION"])
                ssm_client = session.get_client()

                session = Boto3Session(self.logger, account_id=account_id,
                                       service_name='cloudformation', region=os.environ["AWS_REGION"])
                cfn_client = session.get_client()

                self.logger.debug(f'Resolving references in the parameters...')
                parser = Parser()
                resolved_parameters = parser.references(
                    kwargs['event']['StatePayload']['parameters'], self.logger, ssm_client, cfn_client)
                kwargs['event']['StatePayload']['parameters'] = resolved_parameters

            else:
                raise Exception(
                    "Missing service name or the account number in the resource section of the manifest.")

            return func(self, *args, **kwargs)
        return wrapper

    @abstractmethod
    def instantiate_status_check(self):
        pass

    @abstractmethod
    def activate(self):
        pass

    @abstractmethod
    def activate_status_check(self):
        pass

    @abstractmethod
    def replicate():
        pass

    @abstractmethod
    def replicate_status_check(self):
        pass

    @abstractmethod
    def cleanup():
        pass

    @abstractmethod
    def cleanup_status_check(self):
        pass
