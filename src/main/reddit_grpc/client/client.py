import random
import threading
import time

import grpc
import reddit_pb2
import reddit_pb2_grpc


class RedditClient:
    def __init__(self, host, port):
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = reddit_pb2_grpc.RedditServiceStub(self.channel)

    def create_post(self, title, text, author, subreddit_name):
        subreddit = reddit_pb2.Subreddit(name=subreddit_name)
        post = reddit_pb2.Post(title=title, text=text, author=author, subreddit=subreddit)
        return self.stub.CreatePost(reddit_pb2.CreatePostRequest(post=post))

    def vote_post(self, post_id, upvote):
        return self.stub.VotePost(reddit_pb2.VotePostRequest(post_id=post_id, upvote=upvote))

    def retrieve_post(self, post_id):
        return self.stub.RetrievePost(reddit_pb2.RetrievePostRequest(post_id=post_id))

    def create_comment(self, user_id, text, post_id):
        author = reddit_pb2.User(user_id=user_id)
        comment = reddit_pb2.Comment(author=author, text=text)
        return self.stub.CreateComment(reddit_pb2.CreateCommentRequest(comment=comment))

    def vote_comment(self, comment_id, upvote):
        return self.stub.VoteComment(reddit_pb2.VoteCommentRequest(comment_id=comment_id, upvote=upvote))

    def retrieve_top_comments(self, post_id, number_of_comments):
        return self.stub.RetrieveTopComments(
            reddit_pb2.TopCommentsRequest(post_id=post_id, number_of_comments=number_of_comments))

    def expand_comment_branch(self, comment_id, number_of_comments):
        return self.stub.ExpandCommentBranch(
            reddit_pb2.ExpandCommentBranchRequest(comment_id=comment_id, number_of_comments=number_of_comments))

    def monitor_updates(self):
        responses = self.stub.MonitorUpdates(iterate_requests())
        try:
            for response in responses:
                print(f"Update received for item {response.item_id}: new score is {response.new_score}")
        except grpc.RpcError as e:
            print(f"RPC error occurred: {e.code()}")
            print(e.debug_error_string())


def iterate_requests():
    yield reddit_pb2.MonitorUpdatesRequest(post_id="post1")
    yield reddit_pb2.MonitorUpdatesRequest(comment_id="comment1")
    yield reddit_pb2.MonitorUpdatesRequest(comment_id="comment2")
    for i in range(3, 10):
        # Randomly decide whether to add a post or a comment update request
        if random.choice([True, False]):
            yield reddit_pb2.MonitorUpdatesRequest(post_id=f"post{i}")
        else:
            yield reddit_pb2.MonitorUpdatesRequest(comment_id=f"comment{i}")

        # Sleep for a random duration between updates to simulate real-time behavior
        time.sleep(random.randint(1, 3))

# Example usage
if __name__ == "__main__":
    client = RedditClient("localhost", 50059)

    # Test creating a post
    post = client.create_post("Sample Title", "Sample Text", "author1", "subreddit1")
    print(f'Created post with ID: {post.post.id}')

    # Test voting on a post
    post_vote_response = client.vote_post(post.post.id, True)  # True to upvote
    print(f'Voted on post {post.post.id}. New score: {post_vote_response.new_score}')

    # Test retrieving a post
    retrieved_post = client.retrieve_post(post.post.id)
    print(f'Retrieved post: {retrieved_post.post.title}, Score: {retrieved_post.post.score}')

    # Test creating a comment
    comment = client.create_comment("user2", "This is a comment.", post.post.id)
    print(f'Created comment with ID: {comment.comment.id}')

    # Test voting on a comment
    comment_vote_response = client.vote_comment(comment.comment.id, True)  # True to upvote
    print(f'Voted on comment {comment.comment.id}. New score: {comment_vote_response.new_score}')

    # Assume more comments have been created and test retrieving top comments
    top_comments = client.retrieve_top_comments(post.post.id, 2)
    for c in top_comments.comments:
        print(f'Top comment ID: {c.id}, Text: {c.text}, Score: {c.score}')

    # Test expanding a comment branch
    branch = client.expand_comment_branch(comment.comment.id, 2)
    for c in branch.comments:
        print(f'Comment branch ID: {c.id}, Text: {c.text}, Score: {c.score}')

    # Monitor updates - This will run indefinitely
    # Start monitoring updates in a separate thread
    print("Starting to monitor updates...")  # Debug print
    monitor_thread = threading.Thread(target=client.monitor_updates)
    monitor_thread.start()
    monitor_thread.join()  # Optionally wait for the thread to finish, though it runs indefinitely



