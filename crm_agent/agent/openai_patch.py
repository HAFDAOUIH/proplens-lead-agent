"""
OpenAI client patch to handle proxies parameter compatibility.

This patch MUST be imported before any Vanna or OpenAI imports.
Import this module at the top of your Django app initialization.
"""
import openai._base_client as base_client
from openai import OpenAI


def apply_openai_proxies_patch():
    """
    Apply monkey-patch to OpenAI client to ignore proxies parameter.
    
    This is needed because Vanna (or OpenAI library) tries to pass 'proxies'
    parameter to OpenAI client, but newer versions don't accept it.
    Groq doesn't need proxies anyway.
    """
    # Patch SyncHttpxClientWrapper (where the actual error occurs)
    if hasattr(base_client, 'SyncHttpxClientWrapper'):
        if not hasattr(base_client.SyncHttpxClientWrapper.__init__, '_patched'):
            _original_sync_wrapper_init = base_client.SyncHttpxClientWrapper.__init__
            
            def _patched_sync_wrapper_init(self, *args, **kwargs):
                """Patch SyncHttpxClientWrapper.__init__ to ignore proxies parameter."""
                kwargs.pop('proxies', None)
                return _original_sync_wrapper_init(self, *args, **kwargs)
            
            _patched_sync_wrapper_init._patched = True
            base_client.SyncHttpxClientWrapper.__init__ = _patched_sync_wrapper_init
    
    # Patch OpenAI.__init__ as a safety measure
    if not hasattr(OpenAI.__init__, '_patched'):
        _original_openai_init = OpenAI.__init__
        
        def _patched_openai_init(self, *args, **kwargs):
            """Patch OpenAI.__init__ to ignore proxies parameter."""
            kwargs.pop('proxies', None)
            return _original_openai_init(self, *args, **kwargs)
        
        _patched_openai_init._patched = True
        OpenAI.__init__ = _patched_openai_init


# Apply patch immediately when module is imported
apply_openai_proxies_patch()

