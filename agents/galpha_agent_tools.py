import json
from typing import Dict, Any, List


def _is_coord_valid(coords: List[float]) -> bool:
    try:
        if len(coords) < 2:
            return False
        lon, lat = float(coords[0]), float(coords[1])
        return -180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0
    except Exception:
        return False


def geojson_validate(geojson_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ตรวจสอบและวิเคราะห์ GeoJSON:
    - หา features ที่ geometry / property ขาดหาย
    - ตรวจตำแหน่งผิด (lat/lon นอกขอบเขต)
    - ตรวจ duplicate coordinates
    - คืน summary, anomalies, map_actions
    """
    features = geojson_data.get("features", [])
    anomalies = []
    seen_coords = set()
    for idx, feat in enumerate(features, start=1):
        g = feat.get("geometry", {})
        prop = feat.get("properties", {})
        coords = g.get("coordinates", [])
        if not coords or not any(c is not None for c in coords):
            anomalies.append({"index": idx, "reason": "missing coordinates"})
            continue
        if not _is_coord_valid(coords):
            anomalies.append({"index": idx, "reason": "invalid coordinates", "coords": coords})
            continue
        coord_key = (round(float(coords[0]), 6), round(float(coords[1]), 6))
        if coord_key in seen_coords:
            anomalies.append({"index": idx, "reason": "duplicate coordinates", "coords": coords})
        else:
            seen_coords.add(coord_key)
        if not prop or not isinstance(prop, dict):
            anomalies.append({"index": idx, "reason": "missing properties"})
    summary = f"ข้อมูล GeoJSON มี {len(features)} features, พบ anomaly {len(anomalies)} รายการ"
    map_actions = []
    if anomalies:
        map_actions.append({"type": "highlight", "payload": {"indexes": [a["index"] for a in anomalies]}})
        first = anomalies[0]
        if "coords" in first and first["coords"] and len(first["coords"]) >= 2:
            lon, lat = first["coords"][0], first["coords"][1]
            map_actions.append({"type": "zoomTo", "payload": {"center": [lon, lat], "zoom": 12}})
    return {
        "summary": summary,
        "geojson": geojson_data,
        "anomalies": anomalies,
        "map_actions": map_actions
    }
