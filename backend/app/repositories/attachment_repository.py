from app.domain.attachment import AttachmentRecord


class InMemoryAttachmentRepository:
    """Process-local attachment repository for v0.1 mock OCR flow."""

    def __init__(self) -> None:
        self._items: dict[str, AttachmentRecord] = {}

    def save(self, attachment: AttachmentRecord) -> AttachmentRecord:
        self._items[attachment.id] = attachment.model_copy(deep=True)
        return self._items[attachment.id].model_copy(deep=True)

    def get(self, attachment_id: str) -> AttachmentRecord | None:
        attachment = self._items.get(attachment_id)
        if attachment is None:
            return None
        return attachment.model_copy(deep=True)

    def list_by_session(self, session_id: str) -> list[AttachmentRecord]:
        attachments = [
            attachment.model_copy(deep=True)
            for attachment in self._items.values()
            if attachment.session_id == session_id
        ]
        return sorted(
            attachments,
            key=lambda attachment: attachment.created_at,
            reverse=True,
        )

    def clear(self) -> None:
        self._items.clear()


_attachment_repository = InMemoryAttachmentRepository()


def get_attachment_repository() -> InMemoryAttachmentRepository:
    return _attachment_repository
