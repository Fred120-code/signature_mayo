"""Tests for the Streamlit dashboard structure and navigation."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from keys.parameters import K, M, N, O_DIM, V
from streamlit_app import profile_sizes

APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def test_dashboard_loads_home_without_running_crypto() -> None:
    """The home view loads with no cryptographic run or runtime measurement."""
    app = AppTest.from_file(str(APP_PATH)).run()

    assert not app.exception
    assert app.title == []
    assert any("Comprendre la signature" in item.value for item in app.markdown)
    assert not any("Durée totale observée" in item.label for item in app.metric)
    assert not app.button


def test_navigation_opens_development_placeholders() -> None:
    """The unconnected workflow pages are reachable and clearly marked."""
    app = AppTest.from_file(str(APP_PATH)).run()

    for page in ("Génération des clés", "Signature", "Vérification"):
        app.sidebar.radio[0].set_value(page)
        app.run()
        assert not app.exception
        assert any(item.value == page for item in app.title)
        assert any(
            "En cours de développement" in item.value for item in app.info
        )
        assert any(
            "n’affiche aucun résultat cryptographique fictif"
            in " ".join(item.value.split())
            for item in app.markdown
        )


def test_analysis_shows_sizes_from_current_local_profile() -> None:
    """Analysis metrics are derived from the active cryptographic constants."""
    app = AppTest.from_file(str(APP_PATH)).run()
    app.sidebar.radio[0].set_value("Analyse et performances")
    app.run()

    assert not app.exception
    sizes = profile_sizes()
    assert sizes == {
        "compact_public_key": 1168,
        "compact_secret_key": 24,
        "expanded_public_key": 70752,
        "expanded_secret_key": 69856,
        "signature": 321,
    }
    displayed_metrics = {metric.label: metric.value for metric in app.metric}
    assert displayed_metrics["Signature"] == "321 octets"
    assert displayed_metrics["Clé publique compacte"] == "1 168 octets"
    assert displayed_metrics["Clé secrète compacte"] == "24 octets"
    assert f"GF(16) · N={N} · M={M} · K={K}" in {
        item.value for item in app.sidebar.caption
    }
    assert (V, O_DIM) == (58, 8)
    assert not any(
        metric.label == "Durée totale observée" for metric in app.metric
    )
