from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

class Intent(str, Enum):
    SEARCH = "SEARCH"         # Product search
    DETAIL = "DETAIL"         # Specific product details
    QUESTION = "QUESTION"     # General questions about delivery, stores, etc.
    CHIT_CHAT = "CHIT_CHAT"   # Greetings, irrelevant text

class NLUSlots(BaseModel):
    product_name: Optional[str] = Field(None, description="Name of the product to search")
    category: Optional[str] = Field(None, description="Product category")
    price_min: Optional[int] = Field(None, description="Minimum price")
    price_max: Optional[int] = Field(None, description="Maximum price")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Other attributes like color, size")

class NLUResponse(BaseModel):
    intent: Intent = Field(..., description="The primary intent of the user")
    slots: NLUSlots = Field(default_factory=NLUSlots, description="Extracted entities/slots")
    needs_clarification: bool = Field(False, description="True if the request is ambiguous")
    generated_question: Optional[str] = Field(None, description="A follow-up question if clarification is needed")
    confidence: float = Field(0.0, description="Confidence score 0-1")
