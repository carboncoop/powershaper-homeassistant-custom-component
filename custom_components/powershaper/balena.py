import os
import uuid

def get_device_uuid():
    """
    Returns the balena uuid of the device,
    if running a local docker build,
    run before starting docker:
    export BALENA_DEVICE_UUID="chosen_uuid"
    """
    balena_uuid = os.environ["BALENA_DEVICE_UUID"]
    canonical_uuid = uuid.UUID(balena_uuid)
    return str(canonical_uuid)


def get_device_name():
    """
    Returns the balena name of the device,
    if running a local docker build,
    run before starting docker:
    export BALENA_DEVICE_NAME_AT_INIT="chosen_name"
    """
    return os.environ["BALENA_DEVICE_NAME_AT_INIT"]


