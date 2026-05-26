"""
Formatting utilities for Codebase Atlas output.

This module provides functions to format data in both compact and verbose modes,
minimizing context usage while maintaining readability.
"""

from typing import List, Set, Tuple, Optional
from ..models import FileInfo, FunctionInfo, ClassInfo, ImpactNode, RiskLevel
from ..config import AtlasConfig


def format_compact(file_info: FileInfo, config: AtlasConfig) -> List[str]:
    """
    Format FileInfo in ultra-compact notation.
    
    Format:
        F001│main.py│250│⚡
        P: App entry & init
        D: ►F002,F005 ●pygame,numpy
        C: GameManager│[start,update,render,shutdown]
        F: main()→None│load_config(str)→dict
    
    Args:
        file_info: File to format
        config: Atlas configuration
    
    Returns:
        List of formatted lines
    """
    lines = []
    sep = config.compact_symbols['separator']
    
    # Header: F001│main.py│250│⚡
    header = f"{file_info.ref_id}{sep}{file_info.path.name}{sep}{file_info.loc}"
    if file_info.entry_point:
        header += sep + config.compact_symbols['entry_point']
    if file_info.is_react_component:
        header += sep + config.compact_symbols['react_component']
    lines.append(header)
    
    # Purpose: P: Brief description
    if file_info.docstring:
        purpose = truncate_text(file_info.docstring.split('\n')[0], 60)
        lines.append(f"P: {purpose}")
    
    # Dependencies: D: ►F002,F005 ●pygame,numpy
    if file_info.internal_deps or file_info.external_deps:
        dep_parts = []
        if file_info.internal_deps:
            internal_str = ','.join(sorted(file_info.internal_deps))
            dep_parts.append(f"{config.compact_symbols['internal_dep']}{internal_str}")
        if file_info.external_deps:
            external_list = list(file_info.external_deps)[:5]  # Limit to 5
            external_str = ','.join(sorted(external_list))
            if len(file_info.external_deps) > 5:
                external_str += f",+{len(file_info.external_deps)-5}"
            dep_parts.append(f"{config.compact_symbols['external_dep']}{external_str}")
        lines.append(f"D: {' '.join(dep_parts)}")
    
    # Circular dependencies warning
    if file_info.circular_deps:
        circ_str = ','.join(sorted(file_info.circular_deps))
        lines.append(f"⚠️ {config.compact_symbols['circular']}{circ_str}")
    
    # Classes: C: ClassName│[method1,method2,method3]
    for cls in file_info.classes:
        methods_str = ','.join([m.name for m in cls.methods[:10]])  # Limit
        if len(cls.methods) > 10:
            methods_str += f",+{len(cls.methods)-10}"
        base_str = f"←{','.join(cls.bases)}" if cls.bases else ""
        lines.append(f"C: {cls.name}{base_str}{sep}[{methods_str}]")
    
    # Functions: F: func1(args)→ret│func2(args)→ret
    if file_info.functions:
        func_strs = []
        for func in file_info.functions[:15]:  # Limit to 15
            func_strs.append(func.get_signature(compact=True))
        if len(file_info.functions) > 15:
            func_strs.append(f"+{len(file_info.functions)-15}more")
        lines.append(f"F: {sep.join(func_strs)}")
    
    return lines


def format_verbose(file_info: FileInfo, config: AtlasConfig) -> List[str]:
    """
    Format FileInfo in verbose notation.
    
    Args:
        file_info: File to format
        config: Atlas configuration
    
    Returns:
        List of formatted lines
    """
    lines = []
    
    # Header
    icon = _get_file_icon(file_info.ext)
    header = f"#### [{file_info.ref_id}] {icon} `{file_info.path.name}` ({file_info.loc} LOC)"
    if file_info.entry_point:
        header += " ⚡ ENTRY POINT"
    if file_info.is_react_component:
        header += " ⚛️ REACT"
    lines.append(header)
    lines.append("")
    
    # Purpose
    if file_info.docstring:
        lines.append(f"**Purpose:** {file_info.docstring.split(chr(10))[0]}")
        lines.append("")
    
    # Dependencies
    if file_info.internal_deps or file_info.external_deps:
        lines.append("**Dependencies:**")
        if file_info.internal_deps:
            dep_str = ', '.join([f"[{d}]" for d in sorted(file_info.internal_deps)])
            lines.append(f"- Internal: {dep_str}")
        if file_info.external_deps:
            dep_str = ', '.join(sorted(file_info.external_deps))
            lines.append(f"- External: {dep_str}")
        lines.append("")
    
    # Circular deps
    if file_info.circular_deps:
        circ_str = ', '.join(sorted(file_info.circular_deps))
        lines.append(f"⚠️ **Circular Dependencies:** {circ_str}")
        lines.append("")
    
    # Classes
    if file_info.classes:
        lines.append("**Classes:**")
        for cls in file_info.classes:
            base_str = f" extends {', '.join(cls.bases)}" if cls.bases else ""
            lines.append(f"- `{cls.name}`{base_str}")
            if cls.docstring:
                lines.append(f"  - *{cls.docstring.split(chr(10))[0][:80]}*")
            if cls.methods:
                method_names = [m.name for m in cls.methods]
                lines.append(f"  - Methods: [{', '.join(method_names)}]")
        lines.append("")
    
    # Functions
    if file_info.functions:
        lines.append("**Functions:**")
        for func in file_info.functions:
            lines.append(f"- `{func.get_signature(compact=False)}`")
            if func.docstring:
                lines.append(f"  - *{func.docstring.split(chr(10))[0][:80]}*")
        lines.append("")
    
    # Config keys
    if file_info.config_keys:
        keys_str = ', '.join(file_info.config_keys[:10])
        if len(file_info.config_keys) > 10:
            keys_str += f", +{len(file_info.config_keys)-10} more"
        lines.append(f"**Config Keys:** `{keys_str}`")
        lines.append("")
    
    # HTML info
    if file_info.html_analyzed:
        if file_info.template_engine:
            lines.append(f"**Template Engine:** {file_info.template_engine}")
        else:
            lines.append("*Static HTML file*")
        lines.append("")
    
    return lines


def format_function_signature(func: FunctionInfo, compact: bool = False) -> str:
    """
    Format function signature.
    
    Args:
        func: Function to format
        compact: Use compact notation
    
    Returns:
        Formatted signature string
    """
    return func.get_signature(compact=compact)


def format_dependency_list(deps: Set[str], dep_type: str, config: AtlasConfig) -> str:
    """
    Format dependency list.
    
    Args:
        deps: Set of dependency ref IDs or package names
        dep_type: 'internal' or 'external'
        config: Atlas configuration
    
    Returns:
        Formatted string
    """
    if not deps:
        return ""
    
    symbol = (config.compact_symbols['internal_dep'] if dep_type == 'internal'
              else config.compact_symbols['external_dep'])
    
    dep_list = sorted(deps)[:10]  # Limit to 10
    dep_str = ','.join(dep_list)
    
    if len(deps) > 10:
        dep_str += f",+{len(deps)-10}"
    
    return f"{symbol}{dep_str}"


def format_impact_analysis(
    func: FunctionInfo,
    impact: ImpactNode,
    config: AtlasConfig,
    compact: bool = False
) -> List[str]:
    """
    Format impact analysis for a function.
    
    Args:
        func: Function info
        impact: Impact analysis data
        config: Atlas configuration
        compact: Use compact notation
    
    Returns:
        List of formatted lines
    """
    lines = []
    arrow = config.compact_symbols['impact_arrow']
    
    if compact:
        # Compact format: one or two lines
        # ↳Called by: F012,F045 | Calls: F024,F025
        callers = [f"{f}:{fn}" for f, fn in impact.direct_callers]
        calls = [f"{f}:{fn}" for f, fn in impact.direct_calls]
        
        parts = []
        if callers:
            parts.append(f"Called by: {','.join(callers[:3])}")
        if calls:
            parts.append(f"Calls: {','.join(calls[:3])}")
        
        if parts:
            lines.append(f"   {arrow}{' | '.join(parts)}")
        
        # Risk and breaks
        risk_symbol = config.risk_symbols.get(impact.risk_level.value, '')
        breaks = [f"[{f}:{fn}]" for f, fn, _ in impact.get_all_breaks()[:3]]
        
        if breaks:
            lines.append(
                f"   {arrow}Impact: {risk_symbol}{impact.risk_level.value.upper()} "
                f"({impact.total_impact_count} dependents) | "
                f"Breaks: {','.join(breaks)}"
            )
    else:
        # Verbose format: multiple lines with structure
        if impact.direct_callers:
            caller_strs = [f"[{f}] {fn}" for f, fn in impact.direct_callers]
            lines.append(f"  - **Called by:** {', '.join(caller_strs)}")
        
        if impact.direct_calls:
            call_strs = [f"[{f}] {fn}" for f, fn in impact.direct_calls]
            lines.append(f"  - **Calls:** {', '.join(call_strs)}")
        
        if impact.reads_vars:
            lines.append(f"  - **Reads:** {', '.join(sorted(impact.reads_vars))}")
        
        if impact.writes_vars:
            lines.append(f"  - **Writes:** {', '.join(sorted(impact.writes_vars))}")
        
        # Risk assessment
        risk_symbol = config.risk_symbols.get(impact.risk_level.value, '')
        lines.append(
            f"  - **Impact:** {risk_symbol} {impact.risk_level.value.upper()} "
            f"({impact.total_impact_count} dependents)"
        )
        
        # What breaks
        breaks = impact.get_all_breaks()
        if breaks:
            lines.append("  - **Breaks if changed:**")
            for i, (file_ref, func_name, reason) in enumerate(breaks):
                branch = config.compact_symbols['break_last' if i == len(breaks)-1 else 'break_branch']
                lines.append(f"    {branch} [{file_ref}] {func_name} ({reason})")
    
    return lines


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def _get_file_icon(ext: str) -> str:
    """Get emoji icon for file extension."""
    icons = {
        '.py': '🐍',
        '.js': '📜',
        '.jsx': '⚛️',
        '.ts': '📘',
        '.tsx': '⚛️',
        '.html': '🌐',
        '.json': '📋',
        '.yaml': '📋',
        '.yml': '📋',
    }
    return icons.get(ext, '📄')