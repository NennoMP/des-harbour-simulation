import logging
from logging import FileHandler, Formatter

# -------------------------
# LOGGING CONFIGURATION
# -------------------------
LOG_FORMAT = '%(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO

ARRIVAL_LOG_FILE = 'harbour-simulation/data/logs/arrival.log'
DOCK_LOG_FILE = 'harbour-simulation/data/logs/dock.log'
QUEUES_LOG_FILE = 'harbour-simulation/data/logs/queues.log'

# Arrivals Logger
arrival_logger_file_handler = FileHandler(ARRIVAL_LOG_FILE, mode='w')
arrival_logger_file_handler.setLevel(LOG_LEVEL)
arrival_logger_file_handler.setFormatter(Formatter(LOG_FORMAT))

arrival_logger = logging.getLogger('arrivals')
arrival_logger.setLevel(LOG_LEVEL)
arrival_logger.addHandler(arrival_logger_file_handler)


# Docks Logger
dock_logger_file_handler = FileHandler(DOCK_LOG_FILE, mode='w')
dock_logger_file_handler.setLevel(LOG_LEVEL)
dock_logger_file_handler.setFormatter(Formatter(LOG_FORMAT))

dock_logger = logging.getLogger('dockings')
dock_logger.setLevel(LOG_LEVEL)
dock_logger.addHandler(dock_logger_file_handler)

# Queues Logger
queues_logger_file_handler = FileHandler(QUEUES_LOG_FILE, mode='w')
queues_logger_file_handler.setLevel(LOG_LEVEL)
queues_logger_file_handler.setFormatter(Formatter(LOG_FORMAT))

queues_logger = logging.getLogger('queues')
queues_logger.setLevel(LOG_LEVEL)
queues_logger.addHandler(queues_logger_file_handler)
