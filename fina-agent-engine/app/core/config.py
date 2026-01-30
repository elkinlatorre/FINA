# DEPRECATED: This module is deprecated in favor of app.core.settings
# Import from settings instead:
# from app.core.settings import settings

from app.core.settings import settings

# Backwards compatibility - these will be removed in future versions
VALID_SUPERVISORS = settings.VALID_SUPERVISORS
SENSITIVE_FINANCIAL_KEYWORDS = settings.SENSITIVE_FINANCIAL_KEYWORDS
RISK_FINANCIAL_KEYWORDS = settings.RISK_FINANCIAL_KEYWORDS
