from service_module import ServiceModule
from modules import EventBridge, AuroraMySQL, EventArchive, EcsService, R53Record, AutoScaling, ElastiCache, LambdaFunction


# Creator
class ModuleFactory:
    @staticmethod
    def create(service_module: ServiceModule):
        match service_module:
            case ServiceModule.EventBridge:
                return EventBridge()
            case ServiceModule.AuroraMySQL:
                return AuroraMySQL()
            case ServiceModule.EventArchive:
                return EventArchive()
            case ServiceModule.EcsService:
                return EcsService()
            case ServiceModule.R53Record:
                return R53Record()
            case ServiceModule.AutoScaling:
                return AutoScaling()
            case ServiceModule.ElastiCache:
                return ElastiCache()
            case ServiceModule.LambdaFunction:
                return LambdaFunction()                
            case _:
                raise ValueError(
                    f"{service_module} is not currently registered as a module."
                )
