from ingestors import Result
from ..support import TestCase


class ImageIngestorTest(TestCase):

    def test_match(self):
        fixture_path = self.fixture('image.svg')
        result = self.manager.ingest(fixture_path)
        self.assertEqual(result.mime_type, 'image/svg+xml')

    def test_ingest_on_svg(self):
        fixture_path = self.fixture('image.svg')
        result = self.manager.ingest(fixture_path)
        # print result.to_dict()

        self.assertIn(u'TEST', result.body_text)
        # self.assertIn(u'1..2..3..', result.pages[0]['text'])
        self.assertEqual(result.status, Result.STATUS_SUCCESS)

    def test_ingest_hand_written_text(self):
        fixture_path = self.fixture('some hand wirtten veird text.jpg')
        result = self.manager.ingest(fixture_path)

        # self.assert(u'Testing ingestors', result.pages[0]['text'])
        self.assertEqual(result.status, Result.STATUS_SUCCESS)
