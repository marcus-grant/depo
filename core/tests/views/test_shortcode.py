# core/tests/views/test_shortcode.py
from django.urls import reverse
from django.test import TestCase
from django.conf import settings
from pathlib import Path

from core.models.link import LinkItem
from core.models.pic import PicItem
from core.tests.fixtures import PNG_DATA


class ShortcodeDetailsViewTest(TestCase):
    def setUp(self):
        self.link = LinkItem.ensure("https://google.com")
        
        # Setup upload directory for PicItem tests
        self.upload_dir = Path(settings.BASE_DIR) / "test_uploads_shortcode"
        self.upload_dir.mkdir(exist_ok=True)
        settings.UPLOAD_DIR = str(self.upload_dir)
    
    def tearDown(self):
        """Clean up test files"""
        if hasattr(self, 'upload_dir') and self.upload_dir.exists():
            for file in self.upload_dir.iterdir():
                if file.is_file():
                    file.unlink()
            self.upload_dir.rmdir()

    # TODO: Need to figure out how to deal with 404
    # def test_non_existent_shortcode(self):
    #     """Test failed shortcode lookup renders 404-lookup.html"""
    #     resp = self.client.get(reverse("shortcode_details", args=["noExist"]))
    #     self.assertEqual(resp.status_code, 404)
    #     # Because HttPResponseNotFound cant be tested against template use,
    #     # Check for a commented out string with a test marker
    #     self.assertContains(resp, "404-lookup.html", status_code=404)
    #     self.assertContains(resp, "testMarker", status_code=404)

    def test_valid_shortcode_renders_details(self):
        """Test valid shortcode form request renders details page content"""
        shortcode = self.link.item.code
        resp = self.client.get(reverse("item_details", args=[shortcode]))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "shortcode-details.html")
        self.assertContains(resp, shortcode)
        self.assertContains(resp, self.link.url)
    
    def test_picitem_context_structure(self):
        """Test that PicItem details page has correct context structure"""
        # Create a PicItem
        pic = PicItem.ensure(PNG_DATA)
        shortcode = pic.item.code
        
        # Make request to details page
        resp = self.client.get(reverse("item_details", args=[shortcode]))
        
        # Check response
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "shortcode-details.html")
        
        # Check context structure
        self.assertIn('item', resp.context)
        self.assertIn('pic', resp.context)
        
        # Check item context
        item_ctx = resp.context['item']
        self.assertEqual(item_ctx['code'], shortcode)
        self.assertEqual(item_ctx['ctype'], 'pic')
        
        # Check pic context
        pic_ctx = resp.context['pic']
        self.assertIn('url', pic_ctx)
        self.assertIn('format', pic_ctx)
        self.assertIn('size', pic_ctx)
        self.assertEqual(pic_ctx['url'], f"/raw/{shortcode}.{pic.format}")
        self.assertEqual(pic_ctx['format'], 'png')
        self.assertEqual(pic_ctx['size'], len(PNG_DATA))
    
    def test_picitem_renders_image_tag(self):
        """Test that PicItem details page renders an img tag with correct src"""
        # Create a PicItem
        pic = PicItem.ensure(PNG_DATA)
        shortcode = pic.item.code
        
        # Make request to details page
        resp = self.client.get(reverse("item_details", args=[shortcode]))
        
        # Check that image tag is rendered with correct src
        expected_img_src = f"/raw/{shortcode}.{pic.format}"
        self.assertContains(resp, f'<img src="{expected_img_src}"', html=False)
        self.assertContains(resp, 'alt="Image Item"', html=False)
