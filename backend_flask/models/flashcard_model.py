# simple model placeholder (not an ORM in this demo)
from dataclasses import dataclass
from typing import List

@dataclass
class Flashcard:
    question: str
    answer: str
    keywords: List[str]
