"""Runtime patches for the third-party `fitfile` package."""

from __future__ import annotations

import logging
from fitfile.data_message import DataMessage, DataMessageDecodeContext
from fitfile.definition_message import DefinitionMessage
from fitfile.file import File
from fitfile.file_header import FileHeader
from fitfile.message_type import MessageType, UnknownMessageType
from fitfile.record_header import MessageClass, RecordHeader

logger = logging.getLogger(__name__)

_PATCH_ATTR = "_garmindb_skip_unknown_messages"


def _data_payload_size(definition_message: DefinitionMessage) -> int:
    """Return the number of bytes consumed by a data message payload."""
    field_bytes = sum(field_def.size for field_def in definition_message.field_definitions)
    if definition_message.has_dev_fields:
        field_bytes += sum(dev_def.size for dev_def in definition_message.dev_field_definitions)
    return field_bytes


def apply() -> None:
    """Patch `fitfile.file.File` so unknown message types are safely skipped."""
    if getattr(File, _PATCH_ATTR, False):
        logger.debug("fitfile patch already applied")
        return

    def _patched_parse(self: File, file_obj) -> None:  # noqa: PLR0914
        logger.debug("Parsing File %s", self.filename)
        self.file_header = FileHeader(file_obj)
        self.data_size = self.file_header.data_size
        self._definition_messages = {}
        self._File__dev_fields = {}  # type: ignore[attr-defined]
        data_consumed = 0
        self.record_count = 0
        data_message_context = DataMessageDecodeContext()
        while self.data_size > data_consumed:
            record_header = RecordHeader(file_obj)
            local_message_num = record_header.local_message()
            data_consumed += record_header.file_size
            self.record_count += 1
            logger.debug("Parsed record %r", record_header)
            if record_header.message_class is MessageClass.definition:
                definition_message = DefinitionMessage(record_header, self._File__dev_fields, file_obj)  # type: ignore[attr-defined]
                logger.debug("  Definition [%d]: %s", local_message_num, definition_message)
                data_consumed += definition_message.file_size
                self._definition_messages[local_message_num] = definition_message
            else:
                definition_message = self._definition_messages[local_message_num]
                message_type = definition_message.message_type
                if isinstance(message_type, UnknownMessageType):
                    skip_bytes = _data_payload_size(definition_message)
                    file_obj.read(skip_bytes)
                    data_consumed += skip_bytes
                    logger.warning(
                        "Skipping unknown FIT message %s in %s (%d bytes)",
                        message_type,
                        self.filename,
                        skip_bytes,
                    )
                else:
                    data_message = DataMessage(
                        definition_message,
                        file_obj,
                        self.measurement_system,
                        data_message_context,
                    )
                    logger.debug("  Data [%d]: %s", local_message_num, data_message)
                    data_consumed += data_message.file_size
                    data_message_type = data_message.type
                    if data_message_type == MessageType.field_description:
                        self._File__dev_fields[data_message.fields.field_definition_number] = data_message  # type: ignore[attr-defined]
                    logger.debug("Parsed %r", data_message_type)
                    self._File__save_message(data_message_type, data_message)  # type: ignore[attr-defined]
            logger.debug(  # noqa: PLE1205
                "Record %d: consumed %d of %s %r",
                self.record_count,
                data_consumed,
                self.data_size,
                self.measurement_system,
            )
        self.last_message_timestamp = data_message_context.last_timestamp

    File._File__parse = _patched_parse  # type: ignore[attr-defined]
    setattr(File, _PATCH_ATTR, True)
