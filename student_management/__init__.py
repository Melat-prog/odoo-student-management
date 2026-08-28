import psycopg2
import psycopg2.extensions

try:
    # Register a custom adapter for Python str objects that strips NUL bytes
    # BEFORE psycopg2's C-level QuotedString ever sees them.
    # The old approach (patching QuotedString.getquoted) fails because the C
    # code raises ValueError before the Python wrapper runs.

    class _SafeQuotedString(psycopg2.extensions.QuotedString):
        """QuotedString subclass that strips NUL bytes before quoting."""
        def __init__(self, obj):
            if isinstance(obj, str):
                obj = obj.replace('\x00', '')
            elif isinstance(obj, bytes):
                obj = obj.replace(b'\x00', b'')
            super().__init__(obj)

    # Tell psycopg2 to use our adapter for all str objects
    psycopg2.extensions.register_adapter(str, _SafeQuotedString)
except Exception:
    pass

from . import controllers
from . import models