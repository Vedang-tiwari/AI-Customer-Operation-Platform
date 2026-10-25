from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.ticket import Ticket
from app.models.knowledge import KnowledgeDocument
from app.services.ticket_service import process_ticket_ai
from app.core.logging import logger


@celery_app.task(name="process_ticket_task", bind=True, max_retries=3)
def process_ticket_task(self, ticket_id: str):
    """Celery background task for asynchronous ticket processing."""
    db = SessionLocal()
    try:
        ticket = db.get(Ticket, ticket_id)
        if not ticket:
            logger.error(f"Ticket {ticket_id} not found for background processing")
            return
        process_ticket_ai(db, ticket)
        logger.info(f"Successfully processed ticket {ticket_id} in Celery task")
    except Exception as exc:
        logger.error(f"Celery task failed for ticket {ticket_id}: {exc}")
        db.rollback()
        raise self.retry(exc=exc, countdown=5)
    finally:
        db.close()
