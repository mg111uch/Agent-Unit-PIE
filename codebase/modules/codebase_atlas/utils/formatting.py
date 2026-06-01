"""
Formatting utilities for Codebase Atlas output.

Unified format that works for both human readers and LLM agents.
Docstrings are the primary semantic source explaining what code does.
"""

from typing import List, Set, Dict, Optional
from ..models import FileInfo, FunctionInfo, ImpactNode
from ..config import AtlasConfig


def format_file(
    file_info: FileInfo,
    config: AtlasConfig,
    impact_nodes: Optional[Dict[str, ImpactNode]] = None,
) -> List[str]:
    """
    Format FileInfo in unified notation with docstrings.

    Each function is listed individually with its signature, impact analysis,
    and docstring so agents understand behavior without reading source files.

    Format:
        F001│main.py│250│⚡
        S: App entry and init
        D: ►F002,F005 ●pygame,numpy
        C: GameManager│[start,update,render,shutdown]
           S: Manages game state
        F: calculate_damage(attacker,target,crit=False)→int
           ↳Called by: F012,F045 | Calls: F024,F025
           ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F012,F045,F050]
           S: Calculates damage after applying armor and modifiers.

    Args:
        file_info: File to format
        config: Atlas configuration
        impact_nodes: Optional dict of "ref_id:func_name" -> ImpactNode

    Returns:
        List of formatted lines
    """
    lines = []
    sep = config.symbols['separator']

    header = f"{file_info.ref_id}{sep}{file_info.path.name}{sep}{file_info.loc}"
    if file_info.entry_point:
        header += sep + config.symbols['entry_point']
    if file_info.is_react_component:
        header += sep + config.symbols['react_component']
    lines.append(header)

    if file_info.docstring:
        first_line = file_info.docstring.split('\n')[0].strip()
        if first_line:
            lines.append(f"S: {first_line}")

    if file_info.internal_deps or file_info.external_deps:
        dep_parts = []
        if file_info.internal_deps:
            internal_str = ','.join(sorted(file_info.internal_deps))
            dep_parts.append(f"{config.symbols['internal_dep']}{internal_str}")
        if file_info.external_deps:
            external_list = list(file_info.external_deps)[:5]
            external_str = ','.join(sorted(external_list))
            if len(file_info.external_deps) > 5:
                external_str += f",+{len(file_info.external_deps)-5}"
            dep_parts.append(f"{config.symbols['external_dep']}{external_str}")
        lines.append(f"D: {' '.join(dep_parts)}")

    if file_info.circular_deps:
        circ_str = ','.join(sorted(file_info.circular_deps))
        lines.append(f"⚠️ {config.symbols['circular']}{circ_str}")

    for cls in file_info.classes:
        methods_str = ','.join([m.name for m in cls.methods[:10]])
        if len(cls.methods) > 10:
            methods_str += f",+{len(cls.methods)-10}"
        base_str = f"←{','.join(cls.bases)}" if cls.bases else ""
        lines.append(f"C: {cls.name}{base_str}{sep}[{methods_str}]")
        if cls.docstring:
            first_line = cls.docstring.split('\n')[0].strip()
            if first_line:
                lines.append(f"   S: {first_line}")

    for func in file_info.functions[:20]:
        lines.append(f"F: {func.get_signature(compact=True)}")

        if impact_nodes:
            node_key = f"{file_info.ref_id}:{func.name}"
            impact = impact_nodes.get(node_key)
            if impact:
                impact_lines = _format_impact_lines(func, impact, config)
                lines.extend(impact_lines)

        if func.docstring:
            doc_lines = [l.strip() for l in func.docstring.split('\n') if l.strip()]
            for dl in doc_lines[:5]:
                lines.append(f"   S: {dl}")

    if file_info.config_keys:
        keys_str = ', '.join(file_info.config_keys[:10])
        if len(file_info.config_keys) > 10:
            keys_str += f", +{len(file_info.config_keys)-10} more"
        lines.append(f"K: {keys_str}")

    if file_info.html_analyzed and file_info.template_engine:
        lines.append(f"T: {file_info.template_engine}")

    return lines


def format_function_signature(func: FunctionInfo, compact: bool = False) -> str:
    """Format function signature."""
    return func.get_signature(compact=compact)


def format_dependency_list(deps: Set[str], dep_type: str, config: AtlasConfig) -> str:
    """Format dependency list."""
    if not deps:
        return ""

    symbol = (config.symbols['internal_dep'] if dep_type == 'internal'
              else config.symbols['external_dep'])

    dep_list = sorted(deps)[:10]
    dep_str = ','.join(dep_list)

    if len(deps) > 10:
        dep_str += f",+{len(deps)-10}"

    return f"{symbol}{dep_str}"


def _format_impact_lines(
    func: FunctionInfo,
    impact: ImpactNode,
    config: AtlasConfig,
) -> List[str]:
    """
    Format impact analysis lines for a function.

    Format:
       ↳Called by: F012,F045 | Calls: F024,F025
       ↳Impact: 🔴HIGH (3 dependents) | Breaks: [F012,F045,F050]

    Args:
        func: Function info
        impact: Impact analysis data
        config: Atlas configuration

    Returns:
        List of formatted lines
    """
    lines = []
    arrow = config.symbols['impact_arrow']

    callers = [f"{f}:{fn}" for f, fn in impact.direct_callers]
    calls = [f"{f}:{fn}" for f, fn in impact.direct_calls]

    parts = []
    if callers:
        parts.append(f"Called by: {','.join(callers[:3])}")
    if calls:
        parts.append(f"Calls: {','.join(calls[:3])}")

    if parts:
        lines.append(f"   {arrow}{' | '.join(parts)}")

    risk_symbol = config.risk_symbols.get(impact.risk_level.value, '')
    breaks = [f"[{f}:{fn}]" for f, fn, _ in impact.get_all_breaks()[:3]]

    if breaks:
        lines.append(
            f"   {arrow}Impact: {risk_symbol}{impact.risk_level.value.upper()} "
            f"({impact.total_impact_count} dependents) | "
            f"Breaks: {','.join(breaks)}"
        )

    return lines


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
