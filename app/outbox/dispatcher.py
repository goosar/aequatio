from __future__ import annotations

import datetime
import json
import logging
import time
from typing import Iterable, Optional

import pika  # type: ignore[import]
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.persistence.models.outbox import OutboxEvent

log = logging.getLogger("outbox.dispatcher")
log.setLevel(logging.INFO)


class OutboxDispatcher:
    """
    Polls the events_outbox table, publishes events to RabbitMQ,
    and marks them as published.

    Configure via constructor:
      engine: sqlalchemy engine
      rabbit_url: AMQP connection string (e.g. amqp://user:pass@host:5672/vhost)
    """

    def __init__(
        self,
        engine,
        rabbit_url: str,
        batch_size: int = 50,
        poll_interval: float = 2.0,
    ):
        self.engine = engine
        self.SessionLocal = sessionmaker(bind=engine)
        self.rabbit_url = rabbit_url
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self._stopped = False

    def stop(self) -> None:
        self._stopped = True

    def _publish(self, routing_key: str, body: bytes, headers: Optional[dict] = None) -> None:
        """
        Blocking publish using pika. For production consider connection pooling, confirm channels, and retries.
        """
        params = pika.URLParameters(self.rabbit_url)
        conn = pika.BlockingConnection(params)
        try:
            ch = conn.channel()
            # ensure exchange exists (topic)
            ch.exchange_declare(exchange="domain.events", exchange_type="topic", durable=True)
            props = pika.BasicProperties(
                headers=headers or {}, content_type="application/json", delivery_mode=2
            )
            ch.basic_publish(
                exchange="domain.events",
                routing_key=routing_key,
                body=body,
                properties=props,
            )
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _fetch_batch(self, session: Session) -> Iterable[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.created_at)
            .limit(self.batch_size)
            .with_for_update(skip_locked=True)
        )
        res = session.execute(stmt).scalars().all()
        return res

    def run(self) -> None:
        log.info("Outbox dispatcher started")
        while not self._stopped:
            try:
                with self.SessionLocal() as session:
                    events = self._fetch_batch(session)
                    if not events:
                        time.sleep(self.poll_interval)
                        continue

                    for evt in events:
                        try:
                            routing_key = f"{evt.aggregate_type}.{evt.event_type}"
                            body = json.dumps(evt.payload).encode("utf-8")
                            headers = {
                                "event_id": str(evt.id),
                                "event_type": evt.event_type,
                                "aggregate_type": evt.aggregate_type,
                                "aggregate_id": evt.aggregate_id,
                                "event_version": str(evt.event_version),
                            }
                            self._publish(routing_key=routing_key, body=body, headers=headers)

                            # mark published
                            now = datetime.datetime.utcnow()
                            stmt = (
                                update(OutboxEvent)
                                .where(OutboxEvent.id == evt.id)
                                .values(
                                    published_at=now,
                                    attempt_count=evt.attempt_count + 1,
                                    last_error=None,
                                )
                            )
                            session.execute(stmt)
                            session.commit()
                            log.info("Published outbox event %s %s", evt.id, routing_key)
                        except Exception as pub_err:
                            # record failure and allow retries
                            try:
                                now = datetime.datetime.utcnow()
                                stmt = (
                                    update(OutboxEvent)
                                    .where(OutboxEvent.id == evt.id)
                                    .values(
                                        attempt_count=OutboxEvent.attempt_count + 1,
                                        last_error=str(pub_err),
                                    )
                                )
                                session.execute(stmt)
                                session.commit()
                            except Exception as update_err:
                                log.exception(
                                    "Failed updating outbox failure state: %s",
                                    update_err,
                                )
                            log.exception(
                                "Publish failed for outbox event %s: %s",
                                evt.id,
                                pub_err,
                            )
            except SQLAlchemyError as db_err:
                log.exception("Database error in outbox dispatcher: %s", db_err)
                time.sleep(self.poll_interval)
            except Exception as err:
                log.exception("Unexpected error in outbox dispatcher: %s", err)
                time.sleep(self.poll_interval)
        log.info("Outbox dispatcher stopped")


# usage example (not executed here):
#
# from sqlalchemy import create_engine
# engine = create_engine("postgresql://user:pw@host:5432/dbname", future=True)
# dispatcher = OutboxDispatcher(engine=engine, rabbit_url="amqp://guest:guest@localhost:5672/")
# dispatcher.run()
