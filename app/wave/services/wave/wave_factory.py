import logging
from wave.models import Inbound, Outbound

logger = logging.getLogger(__name__)


def create_wave(*, wave_type, user, data):
    logger.debug("create_wave(): %s", wave_type)

    if wave_type == "inbound":
        return Inbound.objects.create(
            stock=data["stock"],
            status=data["status"],
            supplier=data["supplier"].upper().strip(),
            planned_date=data["planned_date"],
            actual_date=data["actual_date"],
            description=data["description"],
            created_by=user,
        )

    if wave_type == "outbound":
        return Outbound.objects.create(
            stock=data["stock"],
            status=data["status"],
            recipient=data["recipient"].upper().strip(),
            planned_date=data["planned_date"],
            actual_date=data["actual_date"],
            description=data["description"],
            created_by=user,
        )

    raise ValueError("Unknown wave_type")
