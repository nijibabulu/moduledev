import click
from colorama import Fore, Style

INTERACT_CLR = Fore.GREEN
GROUP_CLR = Fore.YELLOW
INFO_CLR = Fore.MAGENTA
SETUP_CLR = Fore.RED


class ModuleDevCliMeta(type):
    def __new__(cls, name, bases, dct):
        def _init(self, name, short_help_color=Fore.WHITE, *args, **kwargs):
            super(self.__class__, self).__init__(name, *args, **kwargs)
            self.short_help_color = short_help_color

        def _init_pre7(self, name, short_help_color=Fore.WHITE, *args, **kwargs):
            super(self.__class__, self).__init__(name, *args, **kwargs)
            self.short_help = short_help_color + self.short_help + Style.RESET_ALL

        def _get_short_help_str(self, limit):
            s = super(self.__class__, self).get_short_help_str(limit)
            return self.short_help_color + s + Style.RESET_ALL

        click_major = int(click.__version__.split(".")[0])
        if click_major >= 7:
            dct.update({"__init__": _init, "get_short_help_str": _get_short_help_str})
        else:
            dct.update({"__init__": _init_pre7})
        return super(ModuleDevCliMeta, cls).__new__(cls, name, bases, dct)


class ModuleDevCommand(click.Command, metaclass=ModuleDevCliMeta):
    pass


class ModuleDevGroup(click.Group, metaclass=ModuleDevCliMeta):
    pass
