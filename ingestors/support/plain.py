from ingestors.exc import ProcessingException


class PlainTextSupport(object):
    """Provides helpers for plain text context extraction."""

    def extract_plain_text_content(self, text):
        """Ingestor implementation."""
        try:
            if isinstance(text, str):
                text.encode('utf-8')
            self.result.emit_text_body(text)
        except (UnicodeDecodeError, UnicodeEncodeError) as ue:
            raise ProcessingException('Cannot decode text: %s' % ue)
