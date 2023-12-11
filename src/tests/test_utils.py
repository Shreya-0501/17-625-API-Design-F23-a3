import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add the path to the 'server' directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
client_dir = os.path.join(parent_dir, 'main', 'reddit_grpc', 'client')
sys.path.append(client_dir)

from main.reddit_grpc.client.client import RedditClient
from main.reddit_grpc.client.utils import retrieve_and_expand_comment

class TestRetrieveAndExpandComment(unittest.TestCase):
    @patch('main.reddit_grpc.client.client.RedditClient.retrieve_post')
    @patch('main.reddit_grpc.client.client.RedditClient.retrieve_top_comments')
    @patch('main.reddit_grpc.client.client.RedditClient.expand_comment_branch')
    def test_retrieve_and_expand_comment(self, mock_expand_comment_branch, mock_retrieve_top_comments, mock_retrieve_post):
        # Setup mock responses
        mock_post_response = MagicMock()
        mock_post_response.post.title = "Test Post"
        mock_post_response.post.score = 5
        mock_retrieve_post.return_value = mock_post_response

        mock_comment = MagicMock()
        mock_comment.id = "comment_1"
        mock_comment.score = 10
        mock_retrieve_top_comments.return_value = MagicMock(comments=[mock_comment])

        mock_reply = MagicMock()
        mock_reply.id = "reply_1"
        mock_reply.text = "Test Reply"
        mock_reply.score = 15
        mock_expand_comment_branch.return_value = MagicMock(comments=[mock_comment, mock_reply])

        # Create a RedditClient instance and inject it into the test function
        reddit_client = RedditClient('localhost', 50559)
        result = retrieve_and_expand_comment(reddit_client, 'post_1')

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "reply_1")
        self.assertEqual(result.text, "Test Reply")

if __name__ == '__main__':
    unittest.main()
