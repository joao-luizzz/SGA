import logging
import re


class RecoveryLogFilter(logging.Filter):
    """O servidor de desenvolvimento também registra URLs: ocultar credenciais."""
    def filter(self, record):
        record.msg = re.sub(
            r'(/accounts/reset/)[^/\s]+/[^/\s?"\']+',
            r'\1[redacted]/[redacted]', record.getMessage(),
        )
        record.args = ()
        return True
