import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Add the path to the 'client' directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
client_dir = os.path.join(parent_dir, 'main', 'reddit_grpc', 'client')
sys.path.append(client_dir)

from main.reddit_grpc.client.client import RedditClient
from main.reddit_grpc.client import reddit_pb2, reddit_pb2_grpc

class TestRedditClient(unittest.TestCase):

    def setUp(self):
        self.reddit_client = RedditClient('localhost', 50559)
        self.mock_stub = MagicMock()
        self.reddit_client.stub = self.mock_stub

    def test_create_post(self):
        # Setup
        self.mock_stub.CreatePost.return_value = reddit_pb2.CreatePostResponse(
            post=reddit_pb2.Post(id='post_1', title='Test Post', text='Test Text', score=0)
        )

        response = self.reddit_client.create_post('Test Post', 'Test Text', 'author1', 'subreddit1')

        self.mock_stub.CreatePost.assert_called_once()
        self.assertEqual(response.post.id, 'post_1')
        self.assertEqual(response.post.title, 'Test Post')

    def test_vote_post(self):
        # Setup
        self.mock_stub.VotePost.return_value = reddit_pb2.VotePostResponse(new_score=10)

        # Action
        response = self.reddit_client.vote_post('post_1', True)

        # Assert
        self.mock_stub.VotePost.assert_called_once()
        self.assertEqual(response.new_score, 10)

    def test_retrieve_post(self):
        expected_post = reddit_pb2.Post(id='post_1', title='Test Post', text='Test Text', score=10)
        self.mock_stub.RetrievePost.return_value = reddit_pb2.RetrievePostResponse(post=expected_post)

        response = self.reddit_client.retrieve_post('post_1')

        self.mock_stub.RetrievePost.assert_called_once()
        self.assertEqual(response.post.id, 'post_1')
        self.assertEqual(response.post.title, 'Test Post')

    def test_create_comment(self):
        expected_comment = reddit_pb2.Comment(id='comment_1', text='Test Comment', parent_id='post_1')
        self.mock_stub.CreateComment.return_value = reddit_pb2.CreateCommentResponse(comment=expected_comment)

        response = self.reddit_client.create_comment('user1', 'Test Comment', 'post_1')

        self.mock_stub.CreateComment.assert_called_once()
        self.assertEqual(response.comment.id, 'comment_1')
        self.assertEqual(response.comment.text, 'Test Comment')

    def test_vote_comment(self):
        self.mock_stub.VoteComment.return_value = reddit_pb2.VoteCommentResponse(new_score=5)

        response = self.reddit_client.vote_comment('comment_1', True)

        self.mock_stub.VoteComment.assert_called_once()
        self.assertEqual(response.new_score, 5)

    def test_retrieve_top_comments(self):
        expected_comments = [reddit_pb2.Comment(id='comment_1', text='Test Comment', score=5)]
        self.mock_stub.RetrieveTopComments.return_value = reddit_pb2.RetrieveTopCommentsResponse(comments=expected_comments)

        response = self.reddit_client.retrieve_top_comments('post_1', 1)

        self.mock_stub.RetrieveTopComments.assert_called_once()
        self.assertEqual(len(response.comments), 1)
        self.assertEqual(response.comments[0].id, 'comment_1')

    def test_expand_comment_branch(self):
        expected_comments = [reddit_pb2.Comment(id='comment_1', text='Test Comment', score=5)]
        self.mock_stub.ExpandCommentBranch.return_value = reddit_pb2.ExpandCommentBranchResponse(comments=expected_comments)

        response = self.reddit_client.expand_comment_branch('comment_1', 1)

        self.mock_stub.ExpandCommentBranch.assert_called_once()
        self.assertEqual(len(response.comments), 1)
        self.assertEqual(response.comments[0].id, 'comment_1')

