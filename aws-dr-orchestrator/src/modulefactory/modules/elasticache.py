from .module import Module
from .utils.boto3_session import Boto3Session
import os
import inspect
import sys
import botocore
import re
import time


# ConcreteProductA
class ElastiCache(Module):
    boto3_service_name = "elasticache"
    
    def get_regional_cluster(self, db_cluster_identifiers):
        current_region = os.environ['AWS_REGION']
        regional_cluster_identifier=""
        match current_region:
            case "us-east-1":
                regional_cluster_identifier = f'{db_cluster_identifiers}-{current_region}'
                #regional_cluster_identifier = db_cluster_identifiers
    
            case "us-east-2":
                regional_cluster_identifier = f'{db_cluster_identifiers}-{current_region}'
                
            case "us-west-1":
                regional_cluster_identifier = f'{db_cluster_identifiers}-{current_region}'
                
            case "us-west-2":
                regional_cluster_identifier = f'{db_cluster_identifiers}-{current_region}'
                #regional_cluster_identifier = db_cluster_identifiers
            case _:
                raise Exception('Region Outside United States is not part of logic')
        return {
                'regional_cluster': regional_cluster_identifier
              }
    def get_global_cluster(self, global_cluster_identifier):
        current_region = os.environ['AWS_REGION']
        regional_cluster_identifier=""
        match current_region:
            case "us-east-1":
                global_cluster_identifier = f'ldgnf-{global_cluster_identifier}'
    
            case "us-east-2":
                global_cluster_identifier = f'fpkhr-{global_cluster_identifier}'
                
            case "us-west-1":
                global_cluster_identifier = f'virxk-{global_cluster_identifier}'
                
            case "us-west-2":
                global_cluster_identifier = f'sgaui-{global_cluster_identifier}'
                
            case _:
                raise Exception('Region Outside United States is not part of logic')
        return {
                'global_cluster': global_cluster_identifier
              }
                        
    def get_global_cluster_id_suffix(self, global_cluster_identifier, db_cluster_identifiers):
        try:
            current_region = os.environ['AWS_REGION']
            
            global_cluster_identifier = f'ldgnf-{global_cluster_identifier}'
            
            global_cluster_id_suffix = global_cluster_identifier
            
            check_response = self.service_client.describe_global_replication_groups()
            global_clusters_response = check_response['GlobalReplicationGroups']
            
            global_clusters = []
            for GlobalReplicationGroups in global_clusters_response:
                global_cluster = GlobalReplicationGroups['GlobalReplicationGroupId']
                global_clusters.append(global_cluster)
            
            global_cluster_name = list(filter(lambda global_cluster:re.search(global_cluster_id_suffix, global_cluster), global_clusters))
            
            #if f'ldgnf-{global_cluster_identifier}' in global_cluster_name:
            if global_cluster_identifier in global_cluster_name:
                #global_cluster_name = f'ldgnf-{global_cluster_identifier}'
                global_cluster_name = global_cluster_identifier
                primary_cluster_name = f'{db_cluster_identifiers}-us-east-1'
                #primary_cluster_name = db_cluster_identifiers
                primary_region = 'us-east-1'
                
            #elif f'fpkhr-{global_cluster_identifier}' in global_cluster_name:
            elif global_cluster_identifier in global_cluster_name:
                global_cluster_name = f'fpkhr-{global_cluster_identifier}'
                primary_cluster_name = f'{db_cluster_identifiers}-us-east-2'
                primary_region = 'us-east-2'
                
            #elif f'virxk-{global_cluster_identifier}' in global_cluster_name:
            elif global_cluster_identifier in global_cluster_name:
                global_cluster_name = f'virxk-{global_cluster_identifier}'
                primary_cluster_name = f'{db_cluster_identifiers}-us-west-1'
                primary_region = 'us-west-1'
                
            #elif f'sgaui-{global_cluster_identifier}' in global_cluster_name:
            elif global_cluster_identifier in global_cluster_name:
                #global_cluster_name = f'sgaui-{global_cluster_identifier}'
                global_cluster_name = global_cluster_identifier
                primary_cluster_name = f'{db_cluster_identifiers}-us-west-2'
                #primary_cluster_name = db_cluster_identifiers
                primary_region = 'us-west-2'
                
            else:
                raise Exception("Cannot find global datastore")
            
            return {
                    'global_cluster_name': global_cluster_name
                  }
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
        
    def check_disassociate_status(self, global_cluster_identifier, db_cluster_identifiers):
        global_cluster_name = self.get_global_cluster_id_suffix(self, global_cluster_identifier, db_cluster_identifiers)["global_cluster_name"]
        try:
            response = self.service_client.describe_global_replication_groups(
                        GlobalReplicationGroupId= global_cluster_name
                        )
            
            status_cluster = response['GlobalReplicationGroups'][0]['Status']
            
            return {
                'status': status_cluster
                
              }
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
    
    def check_status_regional(self, db_cluster_identifiers):
        try:
            regional_cluster_identifier = self.get_regional_cluster(self, db_cluster_identifiers)["regional_cluster"]
            response = self.service_client.describe_replication_groups(
                        ReplicationGroupId= regional_cluster_identifier
                        )
            status_regional_cluster = response['ReplicationGroups'][0]['Status']
            return {
                'status': status_regional_cluster
                
              }
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
        
    def disassociate_global_replication_group(self, global_cluster_identifier, db_cluster_identifiers ):
        
        current_region = os.environ['AWS_REGION']
        try:
            regional_cluster_identifier = self.get_regional_cluster(self, db_cluster_identifiers)["regional_cluster"]
            global_cluster_name = self.get_global_cluster_id_suffix(self, global_cluster_identifier, db_cluster_identifiers)["global_cluster_name"]
            response = self.service_client.disassociate_global_replication_group(
                    GlobalReplicationGroupId = global_cluster_name,
                    ReplicationGroupId = regional_cluster_identifier,
                    ReplicationGroupRegion = current_region
                )
            disassociate_status = response['GlobalReplicationGroup']['Status']
            
            return {
                'disassociate_status': disassociate_status
                
              }
            
        except botocore.exceptions.ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
        
    def failover_redis_elasticache(self, global_cluster_identifier, db_cluster_identifiers ):
            try:
                response = self.disassociate_global_replication_group(self, global_cluster_identifier, db_cluster_identifiers)["disassociate_status"]
                status_regcluster = self.check_status_regional(self, db_cluster_identifiers)["status"]
                while (status_regcluster == "Available"):
                    self.check_status_regional(self, db_cluster_identifiers)
                
            except botocore.exceptions.ClientError as error:
                raise error
                
    def global_replication_group_secondary(self, global_cluster_identifier, db_cluster_identifiers):
        try:
            regional_cluster_identifier = self.get_regional_cluster(self, db_cluster_identifiers)["regional_cluster"]
            
            global_datastore_response = self.service_client.create_global_replication_group(
                                    GlobalReplicationGroupIdSuffix = global_cluster_identifier,
                                    GlobalReplicationGroupDescription = 'Global Datatstore',
                                    PrimaryReplicationGroupId = regional_cluster_identifier
                                )
            self.logger.debug(global_datastore_response)
        except botocore.exceptions.ClientError as error:
                raise error
    
    def delete_replicationgroup(self, regional_cluster_identifier):
        try:
            response = self.service_client.delete_replication_group(
            ReplicationGroupId = regional_cluster_identifier,
            RetainPrimaryCluster = False
            )
            self.logger.debug(response)
        except botocore.exceptions.ClientError as error:
            raise error
            
            
    
    def delete_redis_datastore(self, global_cluster_identifier, db_cluster_identifiers):
        regional_cluster_identifier = self.get_regional_cluster(self, db_cluster_identifiers)["regional_cluster"]
        global_cluster_identifier_suffixed = self.get_global_cluster_id_suffix(self, global_cluster_identifier, db_cluster_identifiers)["global_cluster_name"]
        
        try:
            response = self.service_client.delete_global_replication_group(
            GlobalReplicationGroupId = global_cluster_identifier_suffixed,
            RetainPrimaryReplicationGroup = True
             )
            self.logger.debug(response)
            status = self.check_status_regional(self, db_cluster_identifiers)["status"]
        except botocore.exceptions.ClientError as error:
            raise error
        
        
    #def create_new_primary_elasticache(self, session_crossregion, global_cluster_identifier_suffixed, primary_cluster_name, regional_cluster_identifier, db_subnet_group):
    def create_new_primary_elasticache(self, session_crossregion, global_cluster_identifier_suffixed, primary_cluster_name, regional_cluster_identifier):    
        self.service_client_crossregion = session_crossregion.get_client()
        try:
                Primary_cluster_reponse = self.service_client_crossregion.describe_replication_groups(
                    ReplicationGroupId = primary_cluster_name
                )
                
        except botocore.exceptions.ClientError as error:
            raise error    

        
        Redis_Replicas = len(Primary_cluster_reponse['ReplicationGroups'][0]['NodeGroups'][0]['NodeGroupMembers']) - 1
        Redis_Port = Primary_cluster_reponse['ReplicationGroups'][0]['ConfigurationEndpoint']['Port']
        Redis_KMS = Primary_cluster_reponse['ReplicationGroups'][0]['KmsKeyId'].split(":")[5].split("/")[1]


    
        try:
            response = self.service_client.create_replication_group(
                ReplicationGroupId = regional_cluster_identifier,
                ReplicationGroupDescription = 'Regional Cluster for Global Datatstore',
                GlobalReplicationGroupId = global_cluster_identifier_suffixed,
                ReplicasPerNodeGroup = Redis_Replicas,
                Port = Redis_Port,
                #CacheSubnetGroupName = db_subnet_group,
                CacheSubnetGroupName = "redissubnetuseast1",
                KmsKeyId = Redis_KMS,
                PreferredMaintenanceWindow = 'sun:23:00-mon:01:30'
            )
            
            
        except botocore.exceptions.ClientError as error:
            raise error
            
    #def replicate_redis_datastore(self, global_cluster_identifier, db_cluster_identifiers, account_id, boto3_service_name, db_subnet_group):
    def replicate_redis_datastore(self, global_cluster_identifier, db_cluster_identifiers, account_id, boto3_service_name):
        try:
            
            global_clusters_list =[]
            members = []
            global_ds_region = ""
            regional_cluster_identifier = self.get_regional_cluster(self, db_cluster_identifiers)["regional_cluster"]
            response = self.service_client.describe_global_replication_groups()
            
            for item in response['GlobalReplicationGroups']:
                global_clusters_list.append(item['GlobalReplicationGroupId'])
            
            for member in global_clusters_list:
                 members=member.split("-", 1)
                 if members[1] == global_cluster_identifier :
                         
                         if members[0] == "ldgnf":
                             global_ds_region = "us-east-1"
                         if members[0] == "fpkhr":
                             global_ds_region = "us-east-2"
                         if members[0] == "virxk":
                             global_ds_region = "us-west-1"
                         if members[0] == "sgaui":
                             global_ds_region = "us-west-2"
                 
            match global_ds_region:
                case "us-east-1":
                    global_cluster_identifier_suffixed = f'ldgnf-{global_cluster_identifier}'
                    primary_cluster_name = f'{db_cluster_identifiers}-us-east-1'
                case "us-east-2":
                    global_cluster_identifier_suffixed = f'fpkhr-{global_cluster_identifier}'
                    primary_cluster_name = f'{db_cluster_identifiers}-us-east-2'
                case "us-west-1":
                    global_cluster_identifier_suffixed = f'virxk-{global_cluster_identifier}'
                    primary_cluster_name = f'{db_cluster_identifiers}-us-west-1'
                    
                case "us-west-2":
                    session_crossregion = Boto3Session(self.logger, account_id=account_id, service_name=boto3_service_name, region="us-west-2")
                    
                    global_cluster_identifier_suffixed = f'sgaui-{global_cluster_identifier}'
                    primary_cluster_name = f'{db_cluster_identifiers}-us-west-2'
                    #self.create_new_primary_elasticache(self, session_crossregion, global_cluster_identifier_suffixed, primary_cluster_name, regional_cluster_identifier, db_subnet_group)
                    self.create_new_primary_elasticache(self, session_crossregion, global_cluster_identifier_suffixed, primary_cluster_name, regional_cluster_identifier)
                    
                case _:
                    raise Exception('Region Outside United States is not part of logic')
                
               
        except botocore.exceptions.ClientError as error:
            raise error
    @Module.init
    def activate(self, event, boto3_service_name='elasticache'):
        
        db_cluster_identifiers=event['StatePayload']['parameters']['DBClusterIdentifier']
        account_id = event['StatePayload']['parameters']['AccountId']
        global_cluster_identifier=event['StatePayload']['parameters']['GlobalClusterIdentifier']
        
        self.failover_redis_elasticache( self, global_cluster_identifier,
                db_cluster_identifiers )
    
    @Module.init        
    def activate_status_check(self, event, boto3_service_name='elasticache'):
        
        db_cluster_identifiers=event['StatePayload']['parameters']['DBClusterIdentifier']
        global_cluster_identifier=event['StatePayload']['parameters']['GlobalClusterIdentifier']
        status = self.check_disassociate_status(self, global_cluster_identifier, db_cluster_identifiers)
        
        if status['status'] == "primary-only":
            self.global_replication_group_secondary(self, global_cluster_identifier, db_cluster_identifiers)
            
            global_cluster_identifier = f'sgaui-{global_cluster_identifier}'
            try:
                response = self.service_client.describe_global_replication_groups(
                        GlobalReplicationGroupId= global_cluster_identifier
                        )
                
                status_cluster = response['GlobalReplicationGroups'][0]['Status']
                if (status_cluster == "primary-only"):
                    return True
                else:
                    return False
            except botocore.exceptions.ClientError as e:
                self.logger.log_unhandled_exception(e)
                raise
        else:
            return False 
            
        
              
    
    @Module.init
    def cleanup(self, event, boto3_service_name='elasticache'):
        db_cluster_identifiers=event['StatePayload']['parameters']['DBClusterIdentifier']
        regional_cluster_identifier = self.get_regional_cluster(self, db_cluster_identifiers)["regional_cluster"]
        #account_id = event['StatePayload']['parameters']['AccountId']
        global_cluster_identifier=event['StatePayload']['parameters']['GlobalClusterIdentifier']
        self.delete_redis_datastore( self,
                global_cluster_identifier, db_cluster_identifiers
            )
    

    @Module.init
    def cleanup_status_check(self, event, boto3_service_name='elasticache'):
        global_cluster_identifier=event['StatePayload']['parameters']['GlobalClusterIdentifier']
        db_cluster_identifiers=event['StatePayload']['parameters']['DBClusterIdentifier']
        regional_cluster_identifier = self.get_regional_cluster(self, db_cluster_identifiers)["regional_cluster"]

        try:
            self.delete_replicationgroup(self, regional_cluster_identifier)
            response = self.service_client.describe_replication_groups(
                ReplicationGroupId = regional_cluster_identifier
            )
            Status = response['ReplicationGroups'][0]['Status']
            
            if (Status == "Deleting" or "deleting"):
                return True
            else:
                return False
        except botocore.exceptions.ClientError as error:
                raise error  
            
    
    @Module.init
    def replicate(self, event, boto3_service_name='elasticache'):
        db_cluster_identifiers=event['StatePayload']['parameters']['DBClusterIdentifier']
        account_id = event['StatePayload']['parameters']['AccountId']
        global_cluster_identifier=event['StatePayload']['parameters']['GlobalClusterIdentifier']
        #db_subnet_group = event['StatePayload']['parameters']['CacheSubnetGroup']
        #self.replicate_redis_datastore(self, global_cluster_identifier, db_cluster_identifiers, account_id, boto3_service_name, db_subnet_group )
        self.replicate_redis_datastore(self, global_cluster_identifier, db_cluster_identifiers, account_id, boto3_service_name)
        
    @Module.init
    def replicate_status_check(self, event, boto3_service_name='elasticache'):
        
        global_cluster_identifier=event['StatePayload']['parameters']['GlobalClusterIdentifier']
        db_cluster_identifiers=event['StatePayload']['parameters']['DBClusterIdentifier']
        global_cluster_identifier = f'sgaui-{global_cluster_identifier}'
        status = self.check_status_regional(self, db_cluster_identifiers)
        
        if status['status'] == "primary-only":
            return True
        else:
            return False       
    
    
            
    @Module.init
    def instantiate(self, event):
        raise Exception("Instantiate is not applicable to RedisElasticache capability")
    
    @Module.init        
    def instantiate_status_check(self, event):
        raise Exception("Instantiate status check is not applicable to RedisElasticache capability")

            

    
    
    
