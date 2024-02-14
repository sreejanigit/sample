import boto3

user_parameters = {
    # Generic
    "/dr/mdr/account-number:"
    # EventBridge Module parameters
    "/dr/mdr/eventbridge/rule-name": "",
    "/dr/mdr/eventbridge/bus-name": "",
    # EventArchive Module parameters
    "/dr/mdr/eventarchive/archive-arn": "",
    "/dr/mdr/eventarchive/replay-name": "",
    "/dr/mdr/eventarchive/start-time": "",
    "/dr/mdr/eventarchive/end-time": "",
    "/dr/mdr/eventarchive/bus-name":"default"
}

client = boto3.client('ssm')

def add_parameters(parameters):
    for key, value in parameters:
        response = client.put_parameter(
            Name=key,
            Description='Parameter for DR Orchestrator',
            Value=value,
            Type='String',
            Overwrite=True,
            Tier='Standard',
            Policies='string',
            DataType='text'
        )
        return response

if __name__ == "__main__":
    print(add_parameters(user_parameters))