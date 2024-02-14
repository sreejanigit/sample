from .module import Module
from .utils.boto3_session import Boto3Session
import os
import inspect
import sys
import botocore


# ConcreteProductA
class AuroraMySQL(Module):

    boto3_service_name = 'rds'

    def get_db_instance_status(self, db_instance_identifier, db_instance_identifiers):
        try:
            for instance in db_instance_identifiers:
                status = self.service_client.describe_db_instances(DBInstanceIdentifier=instance)[
                    'DBInstances'][0]['DBInstanceStatus']
                self.logger.debug(status)
                if status in ['creating', 'configuring-enhanced-monitoring']:
                    return "CREATING"
                elif status != 'available':
                    raise Exception(
                        f"Aurora DB instance {instance} is not in either creating, configuring-enhanced-monitoring or available state.")
            return 'AVAILABLE'
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def is_headless(self, db_cluster_identifier):

        try:

            db_cluster_members = self.service_client.describe_db_clusters(
                DBClusterIdentifier=db_cluster_identifier)['DBClusters'][0]['DBClusterMembers']
            # db_cluster_members = self.service_client.describe_global_clusters(GlobalClusterIdentifier=db_cluster_identifier)['GlobalClusters'][0]['GlobalClusterMembers']
            self.logger.debug(db_cluster_members)
            if len(db_cluster_members) > 0:
                return {"value": len(db_cluster_members)}
            else:
                return {"value": "HEADLESS"}

        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    # def is_failover_complete(self, db_cluster_identifier):
    #     try:

    #     except ClientError as e:
    #         self.logger.log_unhandled_exception(e)
    #         raise

    def create_headnodes(self, global_cluster_identifier, db_instance_identifiers, db_cluster_identifier):
        try:
            response = self.service_client.describe_global_clusters(
                GlobalClusterIdentifier=global_cluster_identifier
            )
            self.logger.debug(response)

            if self.is_headless(self, db_cluster_identifier)["value"] == "HEADLESS":
                engine = response["GlobalClusters"][0]["Engine"]
                engine_version = response["GlobalClusters"][0]["EngineVersion"]

                for instance in db_instance_identifiers:
                    response = self.service_client.create_db_instance(
                        DBClusterIdentifier=db_cluster_identifier,
                        DBInstanceIdentifier=instance,
                        # DBInstanceIdentifier = db_instance_identifier,
                        DBInstanceClass=f'db.serverless',
                        Engine=engine,
                        EngineVersion=engine_version
                    )
                    self.logger.debug(response)
            else:
                raise Exception("Head nodes already exists")
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def check_failover_status(self, db_cluster_identifier):
        try:
            response_describe_clusters = self.service_client.describe_db_clusters(
                DBClusterIdentifier=db_cluster_identifier)
            db_instances = response_describe_clusters['DBClusters'][0]['DBClusterMembers']
            instance_writer_status = []
            for IsClusterWriter in db_instances:
                status = IsClusterWriter['IsClusterWriter']
                instance_writer_status.append(status)

            if True in instance_writer_status:
                cluster_status = 'PRIMARY CLUSTER'
            elif not instance_writer_status:
                cluster_status = 'HEADLESS CLUSTER'
                raise Exception('HEADLESS CLUSTER')
            elif False in instance_writer_status:
                cluster_status = 'SECONDARY CLUSTER'
            else:
                raise Exception('UNKOWN CLUSTER STATUS')

            return {
                'cluster_status': cluster_status
            }
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def failover_aurora_rds_cluster(self, db_cluster_identifier, account_id, global_cluster_identifier):
        try:
            if self.check_failover_status(self, db_cluster_identifier)["cluster_status"] == "SECONDARY CLUSTER":
                current_region = os.environ['AWS_REGION']
                db_cluster_arn = f'arn:aws:rds:{current_region}:{account_id}:cluster:{db_cluster_identifier}'

                response = self.service_client.failover_global_cluster(
                    GlobalClusterIdentifier=global_cluster_identifier,
                    TargetDbClusterIdentifier=db_cluster_arn,
                    AllowDataLoss=True

                )
            #   return {
            #       'statusCode' :200,
            #       'body' : json.dumps(response)
            #   }

        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def check_delete_db_instance_status(self, db_cluster_identifier):
        try:
            response_describe_instances = self.service_client.describe_db_instances(
                Filters=[
                    {
                        'Name': 'db-cluster-id',
                        'Values': [
                            db_cluster_identifier
                        ]
                    }
                ]
            )
            db_instances = response_describe_instances['DBInstances']
            number_of_db_instances = len(db_instances)
            return {
                'number_of_instances': number_of_db_instances
            }

        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    def delete_db_instances(self, db_cluster_identifier):
        try:
            response_describe_clusters = self.service_client.describe_db_clusters(
                DBClusterIdentifier=db_cluster_identifier)
            db_instances = response_describe_clusters['DBClusters'][0]['DBClusterMembers']
            number_of_db_instances = len(db_instances)
            response_describe_instances = self.service_client.describe_db_instances(
                Filters=[
                    {
                        'Name': 'db-cluster-id',
                        'Values': [
                            db_cluster_identifier
                        ]
                    }
                ]
            )
            db_instances = response_describe_instances['DBInstances']
            number_of_db_instances = len(db_instances)
            response_describe_instances = self.service_client.describe_db_instances(
                Filters=[
                    {
                        'Name': 'db-cluster-id',
                        'Values': [
                            db_cluster_identifier
                        ]
                    }
                ]
            )

            db_instances = response_describe_instances['DBInstances']
            for db_instance in db_instances:
                db_identifier = db_instance['DBInstanceIdentifier']
                self.service_client.delete_db_instance(DBInstanceIdentifier=db_identifier,
                                                       SkipFinalSnapshot=True,
                                                       DeleteAutomatedBackups=True)
            return {
                'statusCode': 200
            }
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise

    @Module.init
    def instantiate(self, event, boto3_service_name='rds'):
        db_cluster_identifier = event['StatePayload']['parameters']['DBClusterIdentifier']
        db_instance_identifiers = event['StatePayload']['parameters']['DBInstanceIdentifier']
        global_cluster_identifier = event['StatePayload']['parameters']['GlobalClusterIdentifier']

        self.create_headnodes(
            self,
            global_cluster_identifier,
            db_instance_identifiers,
            db_cluster_identifier

        )

    @Module.init
    def instantiate_status_check(self, event, boto3_service_name='rds'):
        db_cluster_identifier = event['StatePayload']['parameters']['DBClusterIdentifier']
        db_instance_identifiers = event['StatePayload']['parameters']['DBInstanceIdentifier']
        status = self.get_db_instance_status(
            self, db_cluster_identifier, db_instance_identifiers)
        if status == "AVAILABLE":
            return True
        else:
            return False

    @Module.init
    def activate(self, event, boto3_service_name='rds'):

        db_cluster_identifier = event['StatePayload']['parameters']['DBClusterIdentifier']
        account_id = event['StatePayload']['parameters']['AccountId']
        global_cluster_identifier = event['StatePayload']['parameters']['GlobalClusterIdentifier']
        self.failover_aurora_rds_cluster(self,
                                         db_cluster_identifier, account_id, global_cluster_identifier
                                         )

    @Module.init
    def activate_status_check(self, event, boto3_service_name='rds'):
        db_cluster_identifier = event['StatePayload']['parameters']['DBClusterIdentifier']
        status = self.check_failover_status(self, db_cluster_identifier)
        if status['cluster_status'] == "PRIMARY CLUSTER":
            return True
        else:
            return False

    @Module.init
    def cleanup(self, event, boto3_service_name='rds'):

        db_cluster_identifier = event['StatePayload']['parameters']['DBClusterIdentifier']
        # account_id = event['StatePayload']['parameters']['AccountId']
        global_cluster_identifier = event['StatePayload']['parameters']['GlobalClusterIdentifier']
        self.delete_db_instances(self,
                                 db_cluster_identifier
                                 )

    @Module.init
    def cleanup_status_check(self, event, boto3_service_name='events'):
        db_cluster_identifier = event['StatePayload']['parameters']['DBClusterIdentifier']
        db_instance_identifiers = event['StatePayload']['parameters']['DBInstanceIdentifier']
        status = self.get_db_instance_status(
            self, db_cluster_identifier, db_instance_identifiers)
        if status == "AVAILABLE":
            return True
        else:
            return False

    ### instantiate ###
    def replicate(self, event):
        raise Exception("Instantiate is not applicable to MySQL capability")

    def replicate_status_check(self, event):
        raise Exception("Instantiate is not applicable to MYSQL capability")
