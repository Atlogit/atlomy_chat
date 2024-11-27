"""AMTA: Ancient Medical Text Analysis"""

__version__ = "1.0.0"
__package_name__ = "amta"

# Defer import of run_server to avoid potential circular dependencies
def initialize_server():
    from . import run_server
    return run_server
