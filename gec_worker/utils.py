import json
from dataclasses import dataclass, asdict
from marshmallow import Schema, fields
from typing import Optional, List


class RequestSchema(Schema):
    text = fields.Str(required=True)
    language = fields.Str(required=True)


@dataclass
class Request:
    """
    A dataclass to store requests
    """
    text: str
    language: str


@dataclass
class Span:
    start: int
    end: int


@dataclass
class Replacement:
    value: Optional[str] = None


@dataclass
class Correction:
    span: Span
    replacements: List[Replacement]


@dataclass
class Response:
    """
    A dataclass that can be used to store responses and transfer them over the message queue if needed.
    """
    corrections: Optional[List[Correction]] = None
    status_code: int = 200
    status: str = 'OK'

    def encode(self) -> bytes:
        return json.dumps(asdict(self)).encode()
