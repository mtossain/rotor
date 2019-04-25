import logging
import logging.handlers as handlers

logger = logging.getLogger('my_app')
logger.setLevel(logging.INFO)
logHandler = handlers.RotatingFileHandler('main.log', maxBytes=5000, backupCount=2)
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(logHandler)

logger.info('Information message - Finn is een held')
logger.warning('Warning message')
logger.error('Error message in file')

