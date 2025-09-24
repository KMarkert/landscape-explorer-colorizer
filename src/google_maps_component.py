from typing import Any, Callable, Dict, List, Tuple

import mesop as me

@me.web_component(path="./google_maps_component.js")
def google_maps_component(
    *,
    api_key: str,
    on_click: Callable[[me.WebEvent], Any] | None = None,
    marker: Dict[str, Any] | None = None,
    box: Dict[str, Any] | None = None,
    map_id: str | None = None,
    show_layer: bool = True,
    layer_opacity: float = 1.0,
    key: str | None = None,
):
    """
    A web component wrapper for a Google Map.

    Args:
        api_key: The Google Maps API key.
        on_click: Callback function when the map is clicked (optional).
        marker: A dictionary with lat/lng for the marker.
        box: A dictionary with north, south, east, west for the box.
        map_id: The Earth Engine map ID.
        show_layer: Whether to show the XYZ layer.
        layer_opacity: The opacity of the XYZ layer.
        key: Unique key for the component.
    """
    events = {"clickEvent": on_click}
    properties = {
        "api_key": api_key,
        "marker": marker,
        "box": box,
        "map_id": map_id,
        "show_layer": show_layer,
        "layer_opacity": layer_opacity,
    }
    return me.insert_web_component(
        name="google-maps-component",
        key=key,
        events=events,
        properties=properties,
    )
