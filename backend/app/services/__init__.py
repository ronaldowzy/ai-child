"""Service package initialization."""

from app.services import parent_report_service as _parent_report_service_module
from app.services.parent_report_language_v4_patch import apply_parent_report_language_v4

apply_parent_report_language_v4(_parent_report_service_module)
