import core
from nmrcerm.constants import ACTION_GENERATE_EXPERIMENT_METADATA, ACTION_SEND_METADATA, ACTION_PRINT_PROJECT
from nmrcerm.actions import generate_experiment_metadata, send_metadata, print_project


class Plugin(core.Plugin):

    @classmethod
    def define_args(cls):

        cls.define_arg(ACTION_GENERATE_EXPERIMENT_METADATA, {
            'help': {'usage': '--vid PROJECT_ID',
                     'epilog': '--vid 129'},
            'args': {
                'vid': {'help': 'ARIA visit id',
                        'required': True
                        }
            }
        })


    @classmethod
    def define_methods(cls):
        cls.define_method(ACTION_GENERATE_EXPERIMENT_METADATA, generate_experiment_metadata.perform_action)
        cls.define_method(ACTION_SEND_METADATA, send_metadata.perform_action)
        cls.define_method(ACTION_PRINT_PROJECT, print_project.perform_action)