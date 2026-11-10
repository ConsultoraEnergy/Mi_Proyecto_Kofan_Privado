"""
RBAC por permisos (7.7). Los endpoints exigen permisos concretos, no roles; el mapa rol -> permisos
vive solo aquí.
"""

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    RECEPTIONIST = "receptionist"
    CLIENT = "client"


STAFF_ROLES = frozenset({Role.ADMIN, Role.RECEPTIONIST})


class Permission(StrEnum):
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_MANAGE_STAFF = "users:manage_staff"  # crear/editar admins y recepcionistas, cambiar roles

    ROOMS_READ_ALL = "rooms:read_all"  # incluye habitaciones inactivas
    ROOMS_WRITE = "rooms:write"

    BOOKINGS_READ_ALL = "bookings:read_all"
    BOOKINGS_CREATE_MANUAL = "bookings:create_manual"
    BOOKINGS_UPDATE = "bookings:update"
    BOOKINGS_CHANGE_STATUS = "bookings:change_status"
    BOOKINGS_OVERRIDE_PRICE = "bookings:override_price"
    BOOKINGS_VIEW_RECEIPTS = "bookings:view_receipts"

    FOLIOS_READ = "folios:read"
    FOLIOS_WRITE = "folios:write"

    GALLERY_WRITE = "gallery:write"
    SETTINGS_WRITE = "settings:write"
    DASHBOARD_READ = "dashboard:read"
    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.RECEPTIONIST: frozenset(
        {
            Permission.USERS_READ,
            Permission.USERS_CREATE,
            Permission.USERS_UPDATE,
            Permission.ROOMS_READ_ALL,
            Permission.BOOKINGS_READ_ALL,
            Permission.BOOKINGS_CREATE_MANUAL,
            Permission.BOOKINGS_UPDATE,
            Permission.BOOKINGS_CHANGE_STATUS,
            Permission.BOOKINGS_VIEW_RECEIPTS,
            Permission.FOLIOS_READ,
            Permission.FOLIOS_WRITE,
            Permission.DASHBOARD_READ,
        }
    ),
    Role.CLIENT: frozenset(),
}


def permissions_for(role: str) -> frozenset[Permission]:
    try:
        return ROLE_PERMISSIONS[Role(role)]
    except ValueError:
        return frozenset()


def has_permission(role: str, permission: Permission) -> bool:
    return permission in permissions_for(role)
