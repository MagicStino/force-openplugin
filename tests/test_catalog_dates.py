import unittest
from tools.catalog_bridge import normalize_plugin

class CatalogDates(unittest.TestCase):
 def test_preserves_dates_and_downloads(self):
  raw={'id':'example','name':'Example','repo':'owner/repo','kind':'instrument','updated':'2026-11-06','downloads':123,'versions':[{'version':'1','url':'https://github.com/owner/repo/releases/download/v1/example.zip','sha256':'a'*64,'date':'2026-10-05','downloads':42}]}
  result=normalize_plugin(raw,'fixture')
  self.assertEqual(result['updated'],'2026-11-06')
  self.assertEqual(result['downloads'],123)
  self.assertEqual(result['versions'][0]['date'],'2026-10-05')
  self.assertEqual(result['versions'][0]['downloads'],42)
