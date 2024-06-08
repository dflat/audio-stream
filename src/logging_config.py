import logging
import logging.config

def setup_logging(log_level=logging.INFO):
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '[%(levelname)s]  (%(name)s) :: %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': log_level,
            },
            # add more handlers here (e.g., FileHandler)
        },
        'root': {
            'handlers': ['console'],
            'level': log_level,
        },
        'loggers': {
            '__main__': {
                'handlers': ['console'],
                'level': log_level,
                'propagate': False
            },
        }
    }

    logging.config.dictConfig(logging_config)

