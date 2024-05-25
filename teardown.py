import atexit
import signal
import sys


def register(cleanup_callback):
    # Register with atexit
    register_graceful_exit_on_close(cleanup_callback)
    # Register with signal
    register_graceful_exit_on_kill(cleanup_callback)

# atext handler
def register_graceful_exit_on_close(cleanup_callback):
    # Register with atexit
    atexit.register(cleanup_callback)

# SIGINT / kill / ctrl-C handler
def register_graceful_exit_on_kill(cleanup_callback):
    def signal_handler(signal, frame):
        print(f"Cleaning up and exiting after kill signal: {signal}")
        cleanup_callback()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)