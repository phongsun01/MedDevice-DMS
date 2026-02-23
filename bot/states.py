"""
MedDevice DMS - FSM States for aiogram 3.x
"""
from aiogram.fsm.state import StatesGroup, State


class AddDeviceStates(StatesGroup):
    """Multi-step conversation for adding a new device."""
    category = State()
    device_group = State()
    name = State()
    model = State()
    brand = State()
    origin = State()
    year = State()
    confirm = State()


class CompareStates(StatesGroup):
    """Two-step comparison selection."""
    device_a = State()
    device_b = State()


class UploadStates(StatesGroup):
    """File upload flow."""
    waiting_device = State()
    waiting_file = State()


class SearchStates(StatesGroup):
    """Search pagination."""
    viewing_results = State()
