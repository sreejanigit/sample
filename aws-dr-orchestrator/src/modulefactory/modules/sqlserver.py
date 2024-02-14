from .module import Module
from .utils.boto3_session import Boto3Session
import os
import inspect
import sys
import botocore


# ConcreteProductA
class SQLServer(Module):
    boto3_service_name = "rds"
    
    
    def get_dbinstance_backup(self, db_instance_identifier_source):
        try:
            response = self.service_client.describe_db_instance_automated_backups(
                DBInstanceIdentifier=db_instance_identifier_source
                )
            self.logger.debug(response)
            backup_arn = response['DBInstanceAutomatedBackups'][0]['DBInstanceAutomatedBackupsArn']
            return{
                'db_instance_backup_arn': backup_arn
            }
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
        
    def get_db_instance_status(self, db_instance_identifier):
        try:
            status = self.service_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)['DBInstances'][0]['DBInstanceStatus']
            self.logger.debug(status)
            if status != 'available':
                return "CREATING"
            return 'AVAILABLE'                    
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
        
    def failover_sqlserver(self, db_instance_identifier, db_instance_backup_arn):
        try:
            response = self.service_client.restore_db_instance_to_point_in_time(
                SourceDBInstanceAutomatedBackupsArn =db_instance_backup_arn,
                TargetDBInstanceIdentifier=db_instance_identifier,
                UseLatestRestorableTime=True)
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
    
    def delete_sqlserver_instance(self, db_instance_identifier_source):
        try:
            response = self.service_client.delete_db_instance(
                DBInstanceIdentifier=db_instance_identifier_source,
                DeleteAutomatedBackups=True,
                SkipFinalSnapshot=True
                )
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise    
    
    def start_db_instance_replication(self, db_instance_backup_arn):
        try:
            
            response = self.service_client.start_db_instance_automated_backups_replication(
                SourceDBInstanceArn=db_instance_backup_arn,
                BackupRetentionPeriod=7,
                SourceRegion='us-west-2'
            )
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise            
        
    @Module.init
    def activate(self, event, boto3_service_name=boto3_service_name):
        db_instance_identifier_source=event['StatePayload']['parameters']['DBInstanceIdentifierSource']
        db_instance_identifier=event['StatePayload']['parameters']['DBInstanceIdentifier']
        account_id = event['StatePayload']['AccountId']
        db_instance_backup_arn = self.get_dbinstance_backup(self, db_instance_identifier_source)["db_instance_backup_arn"]
        
        self.failover_sqlserver( self, db_instance_identifier, db_instance_backup_arn)
    
    @Module.init        
    def activate_status_check(self, event, boto3_service_name=boto3_service_name):
        db_instance_identifier=event['StatePayload']['parameters']['DBInstanceIdentifier']
        status = self.get_db_instance_status(self, db_instance_identifier)
        if status == "AVAILABLE":
            return True
        else:
            return False
    
    @Module.init
    def cleanup(self, event, boto3_service_name=boto3_service_name):
        db_instance_identifier_source=event['StatePayload']['parameters']['DBInstanceIdentifier']
        
        self.delete_sqlserver_instance( self,
                db_instance_identifier_source
            )
    
    @Module.init
    def cleanup_status_check(self, event, boto3_service_name=boto3_service_name):
        db_instance_identifier_source=event['StatePayload']['parameters']['DBInstanceIdentifier']
        try:
            status = self.service_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier_source)['DBInstances'][0]['DBInstanceStatus']
            if (status == "Deleting" or "deleting"):
                return True
            else:
                return False
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
    
    
    @Module.init
    def replicate(self, event, boto3_service_name=boto3_service_name):
        db_instance_identifier_source = event['StatePayload']['parameters']['DBInstanceIdentifier']
        #db_instance_backup_arn = self.get_dbinstance_backup(self, db_instance_identifier_source)["db_instance_backup_arn"]
        account_id = event['StatePayload']['AccountId']
        db_instance_backup_arn = f'arn:aws:rds:us-west-2:{account_id}:db:{db_instance_identifier_source}'
        
        self.start_db_instance_replication(self, db_instance_backup_arn)        
        
        
    @Module.init
    def replicate_status_check(self, event, boto3_service_name=boto3_service_name):
        db_instance_identifier_source=event['StatePayload']['parameters']['DBInstanceIdentifier']
        try:
            status = self.service_client.describe_db_instance_automated_backups(DBInstanceIdentifier=db_instance_identifier_source)['DBInstanceAutomatedBackups'][0]['Status']
            if status == "replicating":
                return True
            else:
                return False       
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
    
    
            
    @Module.init
    def instantiate(self, event):
        raise Exception("Activate is not applicable to SqlServer capability")
    
    @Module.init        
    def instantiate_status_check(self, event):
        raise Exception("Activate status check is not applicable to SqlServer capability")
