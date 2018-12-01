import os
import magic
import logging
import hashlib
from normality import stringify
from pantomime import normalize_mimetype, useful_mimetype
from pkg_resources import iter_entry_points

from ingestors.result import Result
from ingestors.directory import DirectoryIngestor
from ingestors.exc import ProcessingException
from ingestors.util import is_file, safe_string

log = logging.getLogger(__name__)


class Manager(object):
    """Handles the lifecycle of an ingestor. This can be subclassed to embed it
    into a larger processing framework."""

    RESULT_CLASS = Result
    MAGIC = magic.Magic(mime=True)
    INGESTORS = []

    def __init__(self, config, ocr_service=None):
        self.config = config
        self._ocr_service = ocr_service

    def get_env(self, name, default=None):
        """Get configuration from local config or environment."""
        value = stringify(self.config.get(name))
        if value is not None:
            return value
        value = stringify(os.environ.get(name))
        if value is not None:
            return value
        return default

    @property
    def ingestors(self):
        if not len(self.INGESTORS):
            for ep in iter_entry_points('ingestors'):
                self.INGESTORS.append(ep.load())
        return self.INGESTORS

    @property
    def ocr_service(self):
        if self._ocr_service is None:
            try:
                from ingestors.services.tesseract import TesseractService
                self._ocr_service = TesseractService()
            except ImportError:
                log.info("Cannot load tesseract OCR service.")
        return self._ocr_service

    def auction(self, file_path, result):
        if not is_file(file_path):
            result.mime_type = DirectoryIngestor.MIME_TYPE
            return DirectoryIngestor

        if not useful_mimetype(result.mime_type):
            mime_type = self.MAGIC.from_file(file_path)
            result.mime_type = normalize_mimetype(mime_type)

        best_score, best_cls = 0, None
        for cls in self.ingestors:
            result.manager = self
            score = cls.match(file_path, result=result)
            if score > best_score:
                best_score = score
                best_cls = cls

        if best_cls is None:
            raise ProcessingException("Format not supported: %s" %
                                      result.mime_type)
        return best_cls

    def before(self, result):
        """Callback called before the processing starts."""
        pass

    def after(self, result):
        """Callback called after the processing starts."""
        pass

    def handle_child(self, parent, file_path, **kwargs):
        result = self.RESULT_CLASS(file_path=file_path, **kwargs)
        parent.children.append(result)
        self.ingest(file_path, result=result)
        return result

    def checksum_file(self, result, file_path):
        "Generate a hash and file size for a given file name."
        if not is_file(file_path):
            return

        if result.checksum is None:
            checksum = hashlib.sha1()
            size = 0
            with open(file_path, 'rb') as fh:
                while True:
                    block = fh.read(8192)
                    if not block:
                        break
                    size += len(block)
                    checksum.update(block)

            result.checksum = checksum.hexdigest()
            result.size = size

        if result.size is None:
            result.size = os.path.getsize(file_path)

    def ingest(self, file_path, result=None, work_path=None):
        """Main execution step of an ingestor."""
        if result is None:
            file_name = os.path.basename(file_path) if file_path else None
            result = self.RESULT_CLASS(file_path=file_path,
                                       file_name=file_name)

        self.checksum_file(result, file_path)
        self.before(result)
        result.status = Result.STATUS_PENDING
        try:
            ingestor_class = self.auction(file_path, result)
            log.debug("Ingestor [%s]: %s", result, ingestor_class.__name__)
            self.delegate(ingestor_class, result, file_path,
                          work_path=work_path)
            result.status = Result.STATUS_SUCCESS
        except ProcessingException as pexc:
            result.error_message = safe_string(pexc)
            result.status = Result.STATUS_FAILURE
            log.warning("Failed [%s]: %s", result, result.error_message)
        finally:
            if result.status == Result.STATUS_PENDING:
                result.status = Result.STATUS_STOPPED
            self.after(result)

        return result

    def delegate(self, ingestor_class, result, file_path, work_path=None):
        ingestor = ingestor_class(self, result, work_path=work_path)
        try:
            ingestor.ingest(file_path)
        finally:
            ingestor.cleanup()
