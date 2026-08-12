"""Run one bounded alert-notification delivery pass."""

from app.core.database import SessionLocal
from app.services.notification_delivery import AlertNotificationDelivery


if __name__ == "__main__":
    with SessionLocal() as db:
        print(AlertNotificationDelivery.deliver_pending(db))
