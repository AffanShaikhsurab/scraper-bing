import unittest
from scrape_bing import BingScraper, SearchResult

class TestBingScraper(unittest.TestCase):
    def setUp(self):
        self.searcher = BingScraper()

    def test_search_results(self):
        results = self.searcher.search("python test", num_results=1)
        self.assertIsInstance(results, list)
        if results:
            self.assertIsInstance(results[0], SearchResult)
            self.assertTrue(results[0].title)
            self.assertTrue(results[0].url)

if __name__ == "__main__":
    unittest.main()