from enum import StrEnum
from uuid import uuid4

from tortoise import fields
from tortoise.models import Model


class ChapterStatus(StrEnum):
    processing = "processing"
    ready = "ready"
    failed = "failed"


class SourceType(StrEnum):
    image = "image"
    link = "link"
    text = "text"


class IngestedChapter(Model):
    id = fields.UUIDField(primary_key=True, default=uuid4)
    child_id = fields.UUIDField()
    subject = fields.CharField(max_length=255)
    school_start_date = fields.DateField()
    segments: list[str] = fields.JSONField(default=list)
    status = fields.CharEnumField(ChapterStatus, default=ChapterStatus.processing)
    reason_code = fields.CharField(max_length=100, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "ingested_chapters"


class RawSource(Model):
    id = fields.UUIDField(primary_key=True, default=uuid4)
    chapter: fields.ForeignKeyRelation[IngestedChapter] = fields.ForeignKeyField(
        "models.IngestedChapter", related_name="sources"
    )
    type = fields.CharEnumField(SourceType)
    raw_ref = fields.TextField()

    class Meta:
        table = "raw_sources"
