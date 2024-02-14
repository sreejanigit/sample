from inspect import getmembers, isclass, isabstract
import modules


# Creator
class DynamicModuleFactory(object):
    # A dictionary to store the available module implementations
    module_dictionary = {}

    def __init__(self):
        self.load_modules()

    def load_modules(self):
        members = getmembers(
            modules, lambda m: isclass(m) and not isabstract(m)
        )
        print(members)
        for name, _type in members:
            if isclass(_type) and issubclass(_type, modules.Module):
                self.module_dictionary[name] = _type

    def create(self, module: str):
        if module in self.module_dictionary:
            return self.module_dictionary[module]()
        else:
            raise ValueError(
                f"{module} is not currently registered as a module"
            )

