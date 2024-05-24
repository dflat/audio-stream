from pynput import keyboard
import time
import sys

class KeyboardListener:
    """
    When being driven by another class, the main api for this
    class is to store it on the host class as e.g.:
        self.keyboard = KeyboardListener(key, start_callback, end_callback)
    and call
        self.keyboard.listen() to start,
        self.keyboard.listening to query if active,
    and self.keyboard.stop_listening() to clean-up underlying listener.
    """
    def __init__(self, key, start_callback, end_callback):
        self.key = key
        self.start_callback = start_callback
        self.end_callback = end_callback
        self.key_active = False
        self.poll_delay = 0.01
        self._init_platform_specific_kb_options()

    def _init_platform_specific_kb_options(self): 
        self.kb_options = { }
        if sys.platform == 'win32':
            self.kb_options['win32_event_filter'] = self.win32_event_filter
        elif sys.platform == 'darwin':
            self.kb_options['darwin_intercept'] = self.darwin_intercept
            

    def on_press(self, key):
        if hasattr(key, 'char') and key.char == self.key:
            if not self.key_active:
                print('key down:', key)
                self.key_active = True
                self.start_callback()

    def on_release(self, key):
        if hasattr(key, 'char') and key.char == self.key:
            if self.key_active:
                print('key up:', key)
                self.key_active = False
                self.end_callback()
                return False  # Stop listener (TODO: remove this and manually call stop_listening?)

    def listen(self):
        self.listener = keyboard.Listener(on_press=self.on_press,
                                          on_release=self.on_release,
                                          **self.kb_options)
        self.listener.start()

    def stop_listening(self):
        self.listener.stop()

    @property
    def listening(self):
        return self.listener.running


    def darwin_intercept(self, event_type, event):
        """
        Macos specific event suppression.
        """
        import Quartz
        length, chars = Quartz.CGEventKeyboardGetUnicodeString(
            event, 100, None, None)
        if length > 0 and chars == self.key:
            # Suppress self.key from printing to terminal
            return None
        elif length > 0 and chars == 'a':
            # Transform a to b
            Quartz.CGEventKeyboardSetUnicodeString(event, 1, 'b')
        else:
            return event

    def win32_event_filter(self, msg, data):
        """
        Values for MSLLHOOKSTRUCT.vkCode can be found here:
        https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
        """
        def get_win32_code(char):
           return ord(char.upper())

        if data.vkCode == get_win32_code(self.key):
            # Suppress self.key from printing to terminal
            self.listener.suppress_event()
