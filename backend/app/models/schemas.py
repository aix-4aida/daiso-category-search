"""Pydantic request/response models"""
from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str


class ProductResult(BaseModel):
    id: int
    rank: int
    name: str
    price: int
    image_url: str
    category_major: str | None = None
    category_middle: str | None = None
    score: float = 0.0
    counter_number: int | None = None
    destination_x: float | None = None
    destination_y: float | None = None
    location_floor: str | None = None
    location_description: str | None = None


class Waypoint(BaseModel):
    x: float
    y: float


class MapInfo(BaseModel):
    floor: str = "1F"
    section: str = ""
    map_image: str = "/static/maps/store.png"
    counter_number: int | None = None
    section_description: str = ""
    destination: Waypoint | None = None
    start: Waypoint | None = None
    waypoints: list[Waypoint] = []


class QueryInfo(BaseModel):
    original: str
    intent: str = "search"
    keywords: list[str] = []


class SearchResponse(BaseModel):
    results: list[ProductResult]
    map_info: MapInfo | None = None
    query_info: QueryInfo | None = None
    message: str | None = None


class ProductResponse(BaseModel):
    id: int
    rank: int
    name: str
    price: int
    image_url: str
    image_name: str | None = None
    category_major: str | None = None
    category_middle: str | None = None


class CategoryResponse(BaseModel):
    major: str
    middles: list[str]


class HealthResponse(BaseModel):
    status: str
    services: dict[str, bool]
