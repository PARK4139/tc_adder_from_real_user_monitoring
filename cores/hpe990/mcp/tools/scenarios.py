"""Public acceptance scenario catalog and traceability."""

import anyio

from cores.common.functions.run_family_bdd import run_family_bdd
from cores.hpe990.functions.scenarios import product_bdd_list, scenario_catalog
from cores.hpe990.functions.step_templates import template_catalog
from cores.hpe990.functions.tc_template_authoring import refresh_templates_from_tcs


def hpe990_tc_templates(
    session_id: str,
    ui_ids: list[str] | None = None,
    refresh_from_tcs: bool = False,
    summary_only: bool = False,
) -> dict:
    """Generate per-UI-ID draft No./Steps/Expected Result groups and JSON/HTML review.

    Covers collected screens, modals/popups and child controls using shared templates.
    Optional ui_ids limits output to observed IDs. Unverified types and absent values,
    ranges/options/outcomes are explicitly pending. No UI actions or TC allocation;
    this does not register executable BDD scenarios or report a test PASS.
    refresh_from_tcs=true regenerates type templates from current authored General TCs
    including save/reopen/restore and invalid-number workflows, then regenerates drafts.
    summary_only=true preserves complete JSON/HTML files and returns counts/paths,
    avoiding transfer of large accumulated draft/evidence lists through MCP.
    """
    refreshed = refresh_templates_from_tcs() if refresh_from_tcs else None
    result = template_catalog(session_id, ui_ids)
    if refreshed:
        result["authored_template_refresh"] = refreshed
    if summary_only:
        return {key: value for key, value in result.items() if key not in ("drafts", "templates")}
    return result


def hpe990_bdd_list() -> dict:
    """List HPE990 product BDD: tagged workflows and authored product TC scenarios.

    Read-only; no session or desktop input required. Returns steps, tags and counts.
    Bound workflows have executable bindings; unbound TCs are authored specifications.
    Review state is not a test result. This tool never executes BDD or reports a PASS.
    """
    return product_bdd_list()


def hpe990_bdd_catalog(session_id: str | None = None) -> dict:
    """Return auto_emulator tool BDD; with session, map the observed HPE990 workflow to steps."""
    return scenario_catalog(session_id)


async def hpe990_bdd_run(allow_desktop_input: bool = False) -> dict:
    """Run registered auto_emulator tool BDD against HPE990 with Real Activity Monitoring and JUnit evidence.

    Requires explicit allow_desktop_input=true. The suite stops only owned HPE990
    sessions, launches fresh sessions, and explicitly stops them during cleanup.
    Zero/skip/xfail/missing/duplicate bindings or tests are failures. Serialized desktop input.
    """
    return await anyio.to_thread.run_sync(run_family_bdd, "auto_emulator", allow_desktop_input)
