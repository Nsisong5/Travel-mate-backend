
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Etinerary(BaseModel):
    day: str
    title: str
    trip_id: int
    items: Optional[List] = []
class EtineraryCreate(Etinerary):
    pass
   
class EtineraryRead(Etinerary):
     id: int