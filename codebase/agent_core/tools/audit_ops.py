import json

try:
    from kernel.signals.signal_engine import signal_engine
    KERNEL_AVAILABLE = True
except ImportError:
    signal_engine = None
    KERNEL_AVAILABLE = False


def emit_tool_compliance_signal(read_count: int, pie_count: int, kernel_read_count: int) -> str:
    if not KERNEL_AVAILABLE or signal_engine is None:
        return "Error: Kernel modules not available. Check kernel installation."

    try:
        value = json.dumps({
            "read_count": read_count,
            "pie_count": pie_count,
            "kernel_read_count": kernel_read_count,
        })

        signal = signal_engine.create_signal(
            signal_type="tool_compliance",
            source_unit_id="agent",
            value=value,
            category="developer_experience",
            title="Tool Compliance Summary",
            description=(
                f"Session ended: {read_count} reads, {pie_count} pie lookups, "
                f"{kernel_read_count} kernel reads"
            ),
        )

        output = {
            "status": "emitted",
            "signal_id": signal.signal_id,
            "signal_type": signal.signal_type,
            "value": signal.value,
        }

        return json.dumps(output, indent=2)

    except Exception as e:
        return f"Error in emit_tool_compliance_signal: {str(e)}"
