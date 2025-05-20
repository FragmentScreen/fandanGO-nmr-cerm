import core
from nmrcerm.constants import ACTION_GENERATE_EXPERIMENT_METADATA
from nmrcerm.actions import generate_experiment_metadata


class Plugin(core.Plugin):

    @classmethod
    def define_args(cls):

        cls.define_arg(ACTION_GENERATE_EXPERIMENT_METADATA, {
            'help': {'usage': '--logs-project-id PROJECT_ID',
                     'epilog': '--logs-project-id 129'},
            'args': {
                'logs-project-id': {'help': 'id of the LOGS project',
                                    'required': True
                                    }
            }
        })

        # cls.define_arg(ACTION_SEND_METADATA, {
        #     'help': {'usage': '--visit-id VISIT_ID',
        #              'epilog': '--visit-id 2'},
        #     'args': {
        #         'visit-id': {'help': 'ARIA visit id',
        #                      'required': True
        #                      }
        #     }
        # })

    @classmethod
    def define_methods(cls):
        cls.define_method(ACTION_GENERATE_EXPERIMENT_METADATA, generate_experiment_metadata.perform_action)