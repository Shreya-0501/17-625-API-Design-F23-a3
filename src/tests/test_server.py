import unittest
from unittest.mock import Mock, patch
import os
import sys

# Add the path to the 'server' directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
server_dir = os.path.join(parent_dir, 'main', 'reddit_grpc', 'server')
sys.path.append(server_dir)

from main.reddit_grpc.server.server import RedditService
from main.reddit_grpc.server import reddit_pb2, reddit_pb2_grpc
class TestRedditService(unittest.TestCase):

    def setUp(self):
        self.service = RedditService()

    def test_create_post(self):
        request = reddit_pb2.CreatePostRequest(
            post=reddit_pb2.Post(title="Test Post", text="Test Content", author="test_author", subreddit=reddit_pb2.Subreddit(name="test_subreddit"))
        )
        context = Mock()  # Mock the gRPC context
        response = self.service.CreatePost(request, context)
        self.assertEqual(response.post.title, "Test Post")
        self.assertEqual(response.post.text, "Test Content")
        self.assertEqual(response.post.author, "test_author")
        self.assertEqual(response.post.subreddit.name, "test_subreddit")

    def test_vote_post(self):
        # Set up the initial state of the post
        post_id = 'post_1'
        initial_score = 0
        self.service.posts[post_id] = reddit_pb2.Post(id=post_id, score=initial_score)

        # Perform the voting action
        request = reddit_pb2.VotePostRequest(post_id=post_id, upvote=True)
        context = Mock()
        response = self.service.VotePost(request, context)

        # Check if the score incremented by 1
        expected_new_score = initial_score + 1
        self.assertEqual(response.new_score, expected_new_score)

    def test_retrieve_post(self):
        # Assuming 'post_1' is already created in the service
        request = reddit_pb2.RetrievePostRequest(post_id='post_1')
        context = Mock()
        response = self.service.RetrievePost(request, context)
        self.assertEqual(response.post.id, 'post_1')
        # Further assertions based on the 'post_1' properties

    def test_create_comment(self):
        request = reddit_pb2.CreateCommentRequest(
            comment=reddit_pb2.Comment(text="Sample comment", parent_id="post_1", author=reddit_pb2.User(user_id="user123"))
        )
        context = Mock()
        response = self.service.CreateComment(request, context)
        self.assertEqual(response.comment.text, "Sample comment")
        self.assertEqual(response.comment.parent_id, "post_1")
        self.assertEqual(response.comment.author.user_id, "user123")

    def test_vote_comment(self):
        comment_id = 'comment_1'
        initial_score = 0
        self.service.comments[comment_id] = reddit_pb2.Comment(id=comment_id, score=initial_score)

        # Perform the voting action
        request = reddit_pb2.VoteCommentRequest(comment_id=comment_id, upvote=True)
        context = Mock()
        response = self.service.VoteComment(request, context)

        # Check if the score incremented by 1
        expected_new_score = initial_score + 1
        self.assertEqual(response.new_score, expected_new_score)

    def test_retrieve_top_comments(self):
        # Assuming 'post_1' and its comments are already created in the service
        request = reddit_pb2.RetrieveTopCommentsRequest(post_id='post_1', number_of_comments=2)
        context = Mock()
        response = self.service.RetrieveTopComments(request, context)
        self.assertTrue(len(response.comments) <= 2)

    def test_expand_comment_branch(self):
        # Assuming 'comment_1' and its replies are already created in the service
        request = reddit_pb2.ExpandCommentBranchRequest(comment_id='comment_1', number_of_comments=2)
        context = Mock()
        response = self.service.ExpandCommentBranch(request, context)
        self.assertTrue(len(response.comments) <= 3)  # Including the main comment

    def test_monitor_updates(self):
        post_id = 'post_1'
        self.service.posts[post_id] = reddit_pb2.Post(id=post_id, title="Sample Post", text="Sample Content", score=0)
        self.service.posts_and_comments[post_id] = 0

        # Mock the streaming behavior
        request_iterator = iter([reddit_pb2.MonitorUpdatesRequest(post_id=post_id)])
        context = Mock()
        responses = list(self.service.MonitorUpdates(request_iterator, context))
        self.assertGreater(len(responses), 0)  # Ensure at least one response is returned


if __name__ == '__main__':
    unittest.main()
