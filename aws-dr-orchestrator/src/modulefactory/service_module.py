from enum import Enum


class ServiceModule(Enum):
    EventBridge = 1
    AuroraMySQL = 2
    EventArchive = 3
    EcsService = 4
    R53Record = 5
    AutoScaling = 6
    ElastiCache = 7
    LambdaFunction = 8

