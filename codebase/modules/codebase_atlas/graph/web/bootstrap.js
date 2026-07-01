// web/bootstrap.js

import { createGraphViewer } from "./graph_viewer.js";

let viewer = null;

function hideLoadingOverlay() {

    const overlay =
        document.getElementById(
            "loading-overlay"
        );

    if (overlay) {
        overlay.classList.add("hidden");
    }
}

function showLoading(message) {

    const overlay =
        document.getElementById(
            "loading-overlay"
        );

    if (overlay) {

        overlay.classList.remove("hidden");
        overlay.textContent = message;
    }
}

function showLoadError(message) {

    const overlay =
        document.getElementById(
            "loading-overlay"
        );

    const status =
        document.getElementById(
            "status-bar"
        );

    if (overlay) {

        overlay.classList.remove("hidden");
        overlay.textContent = message;
    }

    if (status) {
        status.textContent = message;
    }

    console.error(message);
}

function updateSummary(graphData) {

    const summary =
        document.getElementById(
            "graph-summary"
        );

    if (!summary) {
        return;
    }

    const nodes = graphData?.nodes?.length ?? 0;
    const edges = graphData?.edges?.length ?? 0;

    summary.textContent =
        `${nodes} nodes \u00b7 ${edges} edges`;
}

function getGraphData(type) {

    if (type === "call") {
        return window.CALL_GRAPH_DATA;
    }

    return window.GRAPH_DATA;
}

function onGraphTypeChange(event) {

    if (!viewer) {
        return;
    }

    const type = event.target.value;
    const graphData = getGraphData(type);

    if (!graphData) {
        showLoadError(
            "Failed to load graph: no data for type " +
                type
        );
        return;
    }

    showLoading("Switching graph\u2026");

    requestAnimationFrame(() => {

        try {

            viewer.setGraphData(graphData);

            updateSummary(graphData);

            hideLoadingOverlay();

        } catch (error) {

            hideLoadingOverlay();

            showLoadError(
                "Failed to switch graph: " +
                (error?.message ?? String(error))
            );
        }
    });
}

function bindGraphTypeSelect() {

    const select =
        document.getElementById("graph-type");

    if (!select) {
        return;
    }

    select.addEventListener(
        "change",
        onGraphTypeChange
    );
}

function bootstrap() {

    const graphData = window.GRAPH_DATA;

    if (!graphData) {

        showLoadError(
            "Failed to load graph: no data provided"
        );
        return;
    }

    try {

        viewer = createGraphViewer(graphData);

        updateSummary(graphData);
        hideLoadingOverlay();
        bindGraphTypeSelect();

    } catch (error) {

        showLoadError(
            "Failed to render graph: " +
            (error?.message ?? String(error))
        );
    }
}

if (
    document.readyState === "loading"
) {

    document.addEventListener(
        "DOMContentLoaded",
        bootstrap
    );

} else {

    bootstrap();
}
