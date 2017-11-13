import unittest
from SI507project5_code import *


class TestGetData(unittest.TestCase):
    def setUp(self):
        self.ident1 = create_request_identifier("https://api.tumblr.com/v2/blog/", {'blog-identifier': 'hayoubi.tumblr.com', 'method':'posts', 'type': None, 'limit':'20'})
        self.ident2 = create_request_identifier("https://api.tumblr.com/v2/blog/", {'blog-identifier': 'medbutt.tumblr.com', 'method':'posts', 'type': None, 'limit':'20'})
        self.tumblr_data1 = get_data_from_api("https://api.tumblr.com/v2/blog/", "Tumblr", {'blog-identifier': 'hayoubi.tumblr.com', 'method':'posts', 'type': None, 'limit':'20'})

    def test_create_request_identifier(self):
        self.assertEqual(
            self.ident1,
            "https://api.tumblr.com/v2/blog/hayoubi.tumblr.com/posts?api_key=O1kHF4BtrMdtWuFi9CGPwGXiIlR4xFcR6kluaeskPII8eE3j1Q&limit=20",
            "Testing the request identifier is formatted correctly.")
        self.assertEqual(
            self.ident2,
            "https://api.tumblr.com/v2/blog/medbutt.tumblr.com/posts?api_key=O1kHF4BtrMdtWuFi9CGPwGXiIlR4xFcR6kluaeskPII8eE3j1Q&limit=20",
            "Testing the request identifier is formatted correctly.")

    def test_get_data_from_api(self):
        self.assertEqual(len(self.tumblr_data1['response']['posts']), 20, "Testing if the length of retrived data meets the limit params")
        self.assertEqual(self.tumblr_data1['response']['posts'][0]['blog_name'], "hayoubi", "Testing the blog identifier.")
        self.assertEqual(self.tumblr_data1['response']['posts'][0]['type'], "photo", "Testing if the post type is right.")
        self.assertEqual(len(self.tumblr_data1['response']['posts'][0]['tags']), 8, "Testing the number of tags.")

class TestCaching(unittest.TestCase):
    def setUp(self):
        self.data = get_from_cache("https://api.tumblr.com/v2/blog/hayoubi.tumblr.com/posts?api_key=O1kHF4BtrMdtWuFi9CGPwGXiIlR4xFcR6kluaeskPII8eE3j1Q&limit=20", CACHE_DICTION)
        self.data_null = get_from_cache("https://hello.world", CACHE_DICTION)
    def test_get_from_cache(self):
        self.assertEqual(self.data['response']['blog']['name'], "hayoubi", "Test if previous data is in the cache diction.")
        self.assertEqual(self.data['response']['posts'][0]['id'], 165771558644, "Test if previous data is in the cache diction.")
        self.assertIsNone(self.data_null, "Testing if new data is not in the cache diction.")

class TestTumblrPost(unittest.TestCase):
    def setUp(self):
        tumblr_data1 = get_data_from_api("https://api.tumblr.com/v2/blog/", "Tumblr", {'blog-identifier': 'hayoubi.tumblr.com', 'method':'posts', 'type': None, 'limit':'20'})
        self.post_inst = TumblrPost(tumblr_data1['response']['posts'][0])

    def test_constructor(self):
        self.assertEqual(self.post_inst.url, "http://hayoubi.tumblr.com/post/165771558644/hello-sorry-i-dont-post-here-much-anymore-i", "Testing the post instance's url.")
        self.assertEqual(self.post_inst.type, "photo", "Testing the post instance's type.")
        self.assertEqual(self.post_inst.num_tags, 8, "Testing the post instance's num of tags.")
        self.assertEqual(self.post_inst.slug.title(), "Hello Sorry I Dont Post Here Much Anymore I", "Testing the post instance's title.")

    def test_str_method(self):
        self.assertEqual(self.post_inst.__str__(), "hayoubi | photo | http://hayoubi.tumblr.com/post/165771558644/hello-sorry-i-dont-post-here-much-anymore-i")




if __name__ == "__main__":
    unittest.main(verbosity=2)
