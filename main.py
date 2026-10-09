"""
FastAPI application for Assign-7: 10 Closest Locations Recommendation API.
Route: /search/
Fields: (lat, long, cat, rad, link)
"""

import os
from typing import Optional, List, Union, Any
from fastapi import FastAPI, Request, Query, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from service import LocationService

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCATIONS_PATH = os.path.join(BASE_DIR, "locations.csv")
DEFAULT_LINK_PATH = os.path.join(BASE_DIR, "link.txt")

# Initialize Location Service
service = LocationService(LOCATIONS_PATH, DEFAULT_LINK_PATH)

app = FastAPI(
    title="Nearest Location Recommendation API",
    description="CSD Assignment 7 - Grid-based Shortest Path Nearest Locations Recommendation",
    version="1.0.0",
)

# Enable CORS for flexible testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _extract_field(data: dict, *aliases):
    """Helper to extract field value matching any of the alias names (case-insensitive)."""
    if not isinstance(data, dict):
        return None
    lower_data = {str(k).lower(): v for k, v in data.items()}
    for alias in aliases:
        a_low = alias.lower()
        if a_low in lower_data and lower_data[a_low] is not None and lower_data[a_low] != "":
            return lower_data[a_low]
    return None


@app.api_route("/search/", methods=["GET", "POST"])
@app.api_route("/search", methods=["GET", "POST"])
async def search_endpoint(
    request: Request,
    lat: Optional[float] = Query(None),
    long: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    cat: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    CategorySearch: Optional[str] = Query(None),
    rad: Optional[float] = Query(None),
    radius: Optional[float] = Query(None),
    Radius: Optional[float] = Query(None),
    link: Optional[str] = Query(None),
    linkage: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
):
    """
    Search Endpoint accepting inputs:
      (lat, long, cat, rad, link)
    Returns:
      10 recommended location IDs
    """
    # 1. Start with query parameters
    req_lat = lat if lat is not None else latitude
    req_long = long if long is not None else (longitude if longitude is not None else (lon if lon is not None else lng))
    req_cat = cat if cat is not None else (category if category is not None else CategorySearch)
    req_rad = rad if rad is not None else (radius if radius is not None else Radius)
    req_link = link if link is not None else linkage
    req_format = format

    # 2. If POST request, check for JSON or Form data
    if request.method == "POST":
        content_type = request.headers.get("content-type", "").lower()
        
        # Try JSON body
        if "application/json" in content_type:
            try:
                body = await request.json()
                if isinstance(body, dict):
                    req_lat = _extract_field(body, "lat", "latitude") if req_lat is None else req_lat
                    req_long = _extract_field(body, "long", "lon", "lng", "longitude") if req_long is None else req_long
                    req_cat = _extract_field(body, "cat", "category", "CategorySearch") if req_cat is None else req_cat
                    req_rad = _extract_field(body, "rad", "radius", "Radius") if req_rad is None else req_rad
                    req_link = _extract_field(body, "link", "linkage", "link_info", "link_file") if req_link is None else req_link
                    req_format = _extract_field(body, "format") if req_format is None else req_format
            except Exception:
                pass
                
        # Try form data / multipart upload
        elif "form" in content_type or "multipart" in content_type:
            try:
                form_data = await request.form()
                form_dict = dict(form_data)
                req_lat = _extract_field(form_dict, "lat", "latitude") if req_lat is None else req_lat
                req_long = _extract_field(form_dict, "long", "lon", "lng", "longitude") if req_long is None else req_long
                req_cat = _extract_field(form_dict, "cat", "category", "CategorySearch") if req_cat is None else req_cat
                req_rad = _extract_field(form_dict, "rad", "radius", "Radius") if req_rad is None else req_rad
                
                link_val = _extract_field(form_dict, "link", "linkage", "link_info", "link_file")
                if link_val is not None:
                    if hasattr(link_val, "read"):
                        content = await link_val.read()
                        req_link = content.decode("utf-8", errors="replace")
                    else:
                        req_link = str(link_val)
            except Exception:
                pass
        else:
            # Fallback attempt to parse JSON body if content-type header was omitted
            try:
                body = await request.json()
                if isinstance(body, dict):
                    req_lat = _extract_field(body, "lat", "latitude") if req_lat is None else req_lat
                    req_long = _extract_field(body, "long", "lon", "lng", "longitude") if req_long is None else req_long
                    req_cat = _extract_field(body, "cat", "category", "CategorySearch") if req_cat is None else req_cat
                    req_rad = _extract_field(body, "rad", "radius", "Radius") if req_rad is None else req_rad
                    req_link = _extract_field(body, "link", "linkage", "link_info", "link_file") if req_link is None else req_link
            except Exception:
                pass

    # 3. Validate required parameters
    missing = []
    if req_lat is None:
        missing.append("lat")
    if req_long is None:
        missing.append("long")
    if req_cat is None:
        missing.append("cat")
    if req_rad is None:
        missing.append("rad")

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing)}. Required: (lat, long, cat, rad, link)",
        )

    try:
        f_lat = float(req_lat)
        f_long = float(req_long)
        f_rad = float(req_rad)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid numeric input for lat, long, or rad: {e}")

    # 4. Search top 10 recommended locations
    top_10_ids = service.search(
        lat=f_lat,
        lon=f_long,
        cat=str(req_cat),
        rad=f_rad,
        link=req_link,
        top_k=10,
    )

    # 5. Return format
    if req_format in ["dict", "object", "json_object"]:
        return {
            "recommended_locations": top_10_ids,
            "locations": top_10_ids,
            "ids": top_10_ids,
            "count": len(top_10_ids),
        }

    # Standard assignment return: 10 recommended location IDs
    return top_10_ids


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "total_locations": len(service.locations),
        "categories": list(service.cat_to_indices.keys()),
        "default_graph_loaded": len(service.default_adj) > 1,
    }


@app.get("/")
def root():
    return {
        "message": "CSD Assignment 7 - 10 Closest Locations Recommendation API",
        "endpoint": "/search/",
        "required_fields": ["lat", "long", "cat", "rad", "link"],
        "example_query": "/search/?lat=0.505051&long=0.505051&cat=hospital&rad=0.2&link=link.txt",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 6000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
