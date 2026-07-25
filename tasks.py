from celery import shared_task
from celery.utils.log import get_task_logger
from .services import run_unified_sync

logger = get_task_logger(__name__)


@shared_task(name="integrationservices.tasks.run_cmms_sync_task")
def run_cmms_sync_task(steps=None):
    """
    Celery task that executes the Unified CMMS Synchronization workflow.

    Parameters
    ----------
    steps : list[str] | None
        Optional subset of phases to run, e.g. ["masters", "push"].
        Defaults to all three phases (masters → push → approvals).
    """
    logger.info(
        f"Executing scheduled CMMS synchronization task. Phases: {steps or 'all'}"
    )
    result = run_unified_sync(steps=steps)
    logger.info(
        f"CMMS synchronization task completed. "
        f"sync_id={result.get('sync_id')} "
        f"status={result.get('status')} "
        f"duration={result.get('duration_seconds')}s"
    )
    return result
