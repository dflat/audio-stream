import atexit

def register(cleanup_func):
    # Register with atexit
    atexit.register(cleanup_func)

def register_ipython(cleanup_func): # not working
    # Register with IPython if available
    ip = get_ipython()
    if ip is not None:
        def ipython_cleanup():
            print("Running IPython cleanup...")
            cleanup_func()

        ip.events.register('terminal', ipython_cleanup)
