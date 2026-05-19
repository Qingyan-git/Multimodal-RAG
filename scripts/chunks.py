from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Chunk:

    id : Optional[int] = None

    document_name : Optional[str] = ""

    page_no : Optional[list] = field(default_factory=list)

    context : Optional[str] = ""

    content : Optional[str] = ""
