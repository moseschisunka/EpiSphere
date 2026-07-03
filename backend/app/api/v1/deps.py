"""Compatibility re-exports for API dependencies.

New code should import from app.core.dependencies directly.
"""

from app.core.dependencies import (  # noqa: F401
    RoleChecker,
    allow_admin,
    allow_clinician,
    allow_facility_admin,
    allow_pharmacist,
    get_current_active_user,
    get_current_facility_user,
    require_role,
)
