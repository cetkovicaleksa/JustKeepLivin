# import os
# import logging

# _logger = logging.getLogger(__name__)

# _MOCK = os.getenv('GPIOHERO_MOCK')

# if _MOCK is not None:
#     _logger.info("`GPIOHERO_MOCK` env variable is set, all devices will be mocked.")
    
#     # <https://gpiozero.readthedocs.io/en/stable/api_pins.html#mock-pins>
#     os.environ['GPIOZERO_PIN_FACTORY'] = 'mock'

