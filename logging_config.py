import logging
import logging.config

def setup_logging(loglevel=logging.INFO):
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': loglevel,
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
            },
            'file': {
                'level': loglevel,
                'class': 'logging.FileHandler',
                'formatter': 'standard',
                'filename': '/tmp/wp-scanner.log',
                'mode': 'a',
            },
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': loglevel,
        },
    }

    logging.config.dictConfig(logging_config)
