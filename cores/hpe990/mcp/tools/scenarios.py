"""Public acceptance scenario catalog and traceability."""

import anyio

from cores.common.functions.run_family_bdd import run_family_bdd
from cores.hpe990.functions.scenarios import scenario_catalog


def hpe990_bdd_catalog(session_id: str | None = None) -> dict:
    """Return registered Gherkin/bindings; with session, map its observed workflow to scenario steps."""
    return scenario_catalog(session_id)


async def hpe990_bdd_run(allow_desktop_input: bool = False) -> dict:
    """Run all registered actual Emulator acceptance scenarios with RAM and durable JUnit evidence.

    Requires explicit allow_desktop_input=true. The suite stops only owned HPE990
    sessions, launches fresh sessions, and explicitly stops them during cleanup.
    Zero/skip/xfail/missing/duplicate bindings or tests are failures. Serialized desktop input.
    """
    return await anyio.to_thread.run_sync(run_family_bdd, "hpe990", allow_desktop_input)
