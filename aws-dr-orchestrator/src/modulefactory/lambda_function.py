from dynamic_module_factory import DynamicModuleFactory
from module_factory import ModuleFactory
from service_module import ServiceModule


# Client
def lambda_handler(event, context):
    factory = DynamicModuleFactory()
    module = factory.create(event['StatePayload']['action'])
    if 'status' in event:
        return module.call_lifecycle(name=f"{event['LifeCyclePhase']}_status_check", event=event)
    else:
        return module.call_lifecycle(name=event['LifeCyclePhase'], event=event)

