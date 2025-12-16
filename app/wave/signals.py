import logging
import os
import shutil

from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Inbound, Outbound

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=Inbound)
def delete_inbound_documents(sender, instance, **kwargs):
    """Удаляет папку с именем inbound.inbound_number после удаления Inbound."""
    if not instance.inbound_number:
        return

    inbound_folder = instance.get_uploads_dir()
    if os.path.exists(inbound_folder) and os.path.isdir(inbound_folder):
        try:
            shutil.rmtree(inbound_folder)
            logger.debug("Folder %s successfully deleted", inbound_folder)
        except Exception as e:
            logger.error(f"Error deleting folder {inbound_folder}: {e}")


@receiver(post_delete, sender=Outbound)
def delete_outbound_documents(sender, instance, **kwargs):
    """Удаляет папку с именем outbound.outbound_number после удаления Outbound."""
    if not instance.outbound_number:
        return

    outbound_folder = instance.get_uploads_dir()
    if os.path.exists(outbound_folder) and os.path.isdir(outbound_folder):
        try:
            shutil.rmtree(outbound_folder)
            logger.debug("Folder %s successfully deleted", outbound_folder)
        except Exception as e:
            logger.error(f"Error deleting folder {outbound_folder}: {e}")
