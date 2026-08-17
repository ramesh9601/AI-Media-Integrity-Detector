from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class FileInfo(BaseModel):
    original_name: str
    saved_name: str
    file_type: str


class ResultInfo(BaseModel):
    prediction: str
    integrity_score: float
    color: str
    reasons: List[str]


class ForensicsInfo(BaseModel):
    image: Dict[str, Any]
    exif: Dict[str, Any]
    ela: Dict[str, Any]
    noise: Dict[str, Any]
    copy_move: Dict[str, Any]


class ReportInfo(BaseModel):
    pdf: str


class UploadResponse(BaseModel):
    success: bool
    message: str
    file: FileInfo
    result: ResultInfo
    forensics: ForensicsInfo
    report: ReportInfo