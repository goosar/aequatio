"""Event handlers for user domain events.

This module contains handlers that react to user-related domain events.
Event handlers should be side-effect operations that happen AFTER the
main transaction commits (welcome emails, analytics, etc.).
"""

import logging
from typing import Any, Dict

from app.domain.events.schema import UserRegisteredPayload

logger = logging.getLogger(__name__)


class UserEventHandler:
    """Handler for user domain events.

    This class processes user-related events published to the message broker.
    All operations here should be idempotent (safe to retry) since events
    may be delivered multiple times.
    """

    async def handle_user_registered(self, event_data: Dict[str, Any]) -> None:
        """Handle user registration event.

        This is called when a UserRegisteredPayload event is consumed from
        the message broker (RabbitMQ). It should trigger all post-registration
        side effects.

        Args:
            event_data: Event payload dictionary.

        Example:
            >>> handler = UserEventHandler()
            >>> await handler.handle_user_registered({
            ...     "user_id": 123,
            ...     "username": "john_doe",
            ...     "email": "john@example.com"
            ... })
        """
        # Parse event payload
        payload = UserRegisteredPayload(**event_data)

        logger.info(f"Processing user registration event for user_id={payload.user_id}")

        try:
            # Side effect 1: Send welcome email
            await self._send_welcome_email(payload)

            # Side effect 2: Track in analytics
            await self._track_analytics(payload)

            # Side effect 3: Initialize user preferences
            await self._initialize_preferences(payload)

            logger.info(f"Successfully processed registration for user_id={payload.user_id}")

        except Exception as e:
            # Log error but don't fail - these are side effects
            # Event will be retried by the outbox dispatcher
            logger.error(
                f"Error processing user registration for user_id={payload.user_id}: {e}",
                exc_info=True,
            )
            raise  # Re-raise to trigger retry

    async def _send_welcome_email(self, payload: UserRegisteredPayload) -> None:
        """Send welcome email to newly registered user.

        Args:
            payload: User registration event data.
        """
        # TODO: Integrate with email service (SendGrid, AWS SES, etc.)
        logger.info(f"[EMAIL] Sending welcome email to {payload.email} (user_id={payload.user_id})")

        # Pseudo-code for actual implementation:
        # email_service = EmailService()
        # await email_service.send_template(
        #     to=payload.email,
        #     template="welcome",
        #     data={"username": payload.username}
        # )

    async def _track_analytics(self, payload: UserRegisteredPayload) -> None:
        """Track user registration in analytics platform.

        Args:
            payload: User registration event data.
        """
        # TODO: Integrate with analytics (Mixpanel, Segment, etc.)
        logger.info(
            f"[ANALYTICS] Tracking registration for user_id={payload.user_id}, "
            f"IP={payload.metadata.get('ip_address')}, "
            f"User-Agent={payload.metadata.get('user_agent')}"
        )

        # Pseudo-code for actual implementation:
        # analytics = AnalyticsClient()
        # await analytics.track(
        #     user_id=payload.user_id,
        #     event="user_registered",
        #     properties={
        #         "username": payload.username,
        #         "email": payload.email,
        #         "ip_address": payload.metadata.get("ip_address"),
        #         "timestamp": payload.timestamp.isoformat()
        #     }
        # )

    async def _initialize_preferences(self, payload: UserRegisteredPayload) -> None:
        """Initialize default user preferences.

        Args:
            payload: User registration event data.
        """
        # TODO: Create default user preferences in database
        logger.info(f"[PREFERENCES] Initializing default preferences for user_id={payload.user_id}")

        # Pseudo-code for actual implementation:
        # preferences_repo = UserPreferencesRepository(db)
        # default_prefs = UserPreferences(
        #     user_id=payload.user_id,
        #     theme="light",
        #     notifications_enabled=True,
        #     language="en"
        # )
        # await preferences_repo.save(default_prefs)


# Event routing map - maps event types to handlers
EVENT_HANDLERS = {
    "user.registered": UserEventHandler().handle_user_registered,
    # Add more event handlers here:
    # "user.email_changed": UserEventHandler().handle_email_changed,
    # "expense.created": ExpenseEventHandler().handle_expense_created,
}


async def dispatch_event(event_type: str, event_data: Dict[str, Any]) -> None:
    """Dispatch an event to the appropriate handler.

    This is the entry point for the event consumer (RabbitMQ subscriber).
    It routes events to the correct handler based on event type.

    Args:
        event_type: Type of event (e.g., "user.registered").
        event_data: Event payload data.

    Raises:
        ValueError: If event type has no registered handler.

    Example:
        >>> await dispatch_event("user.registered", {
        ...     "user_id": 123,
        ...     "username": "john",
        ...     "email": "john@example.com"
        ... })
    """
    handler = EVENT_HANDLERS.get(event_type)

    if not handler:
        logger.warning(f"No handler registered for event type: {event_type}")
        raise ValueError(f"No handler for event type: {event_type}")

    logger.info(f"Dispatching event {event_type} to handler")
    await handler(event_data)
