import queue
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
        self.known_posts = {f'post_{i}' for i in range(1, 5)}
        self.known_comments = {f'comment_{i}' for i in range(1, 10)}


    def setup_data(self):
        # Creating posts
        posts = [
            {"title": "Carnegie Mellon's history", "content": "In 1967, Carnegie Tech merged with the Mellon Institute...", "author": "author1", "subreddit": "subreddit1"},
            {"title": "Carnegie Institute of Technology", "content": "During the first half of the 20th century...", "author": "author2", "subreddit": "subreddit1"},
            {"title": "School of Computer Science", "content": "Carnegie Mellon’s School of Computer Science is...", "author": "author5", "subreddit": "subreddit2"}
        ]

        for post in posts:
            response = self.create_post(post["title"], post["content"], post["author"], post["subreddit"])
            print(f'Created post with ID: {response.post.id}')
            self.known_posts.add(response.post.id)

        # Creating comments and nested comments
        comments = [
            {"user_id": "user2", "text": "This is a comment.", "parent_id": "post_1"},
            {"user_id": "user3", "text": "Nested comment.", "parent_id": "comment_1"}
            # Add more comments as needed
        ]

        for comment in comments:
            response = self.create_comment(comment["user_id"], comment["text"], comment["parent_id"])
            print(f'Created comment with ID: {response.comment.id}')
            self.known_comments.add(response.comment.id)

        # Voting on posts and comments
        for post_id in self.known_posts:
            self.vote_post(post_id, True)  # Upvoting all posts
        for comment_id in self.known_comments:
            self.vote_comment(comment_id, True)  # Upvoting all comments

        # Retrieving posts and top comments
        for post_id in self.known_posts:
            retrieved_post = self.retrieve_post(post_id)
            print(f'Retrieved post: {retrieved_post.post.title}, Score: {retrieved_post.post.score}')
            top_comments = self.retrieve_top_comments(post_id, 2)
            for c in top_comments.comments:
                replies_status = "has replies" if c.has_replies else "no replies"
                print(f'Top comment ID: {c.id}, Text: {c.text}, Score: {c.score}, Status: {replies_status}')

        # Expanding comment branches
        for comment_id in self.known_comments:
            branch = self.expand_comment_branch(comment_id, 2)
            main_comment_printed = False
            for c in branch.comments:
                if not main_comment_printed:
                    print(f'Main Comment ID: {c.id}, Text: {c.text}, Score: {c.score}')
                    main_comment_printed = True
                else:
                    print(f'  Reply ID: {c.id}, Text: {c.text}, Score: {c.score}')


    def create_post(self, title, text, author, subreddit_name):
        subreddit = reddit_pb2.Subreddit(name=subreddit_name)
        post = reddit_pb2.Post(title=title, text=text, author=author, subreddit=subreddit)
        response = self.stub.CreatePost(reddit_pb2.CreatePostRequest(post=post))
        self.known_posts.add(response.post.id)
        return response

    def vote_post(self, post_id, upvote):
        response = self.stub.VotePost(reddit_pb2.VotePostRequest(post_id=post_id, upvote=upvote))
        return response

    def retrieve_post(self, post_id):
        response = self.stub.RetrievePost(reddit_pb2.RetrievePostRequest(post_id=post_id))
        return response

    def create_comment(self, user_id, text, parent_id):
        author = reddit_pb2.User(user_id=user_id)
        comment = reddit_pb2.Comment(author=author, text=text, parent_id=parent_id)
        response = self.stub.CreateComment(reddit_pb2.CreateCommentRequest(comment=comment))
        self.known_comments.add(response.comment.id)
        return response

    def vote_comment(self, comment_id, upvote):
        response = self.stub.VoteComment(reddit_pb2.VoteCommentRequest(comment_id=comment_id, upvote=upvote))
        return response

    def retrieve_top_comments(self, post_id, number_of_comments):
        response = self.stub.RetrieveTopComments(reddit_pb2.RetrieveTopCommentsRequest(post_id=post_id, number_of_comments=number_of_comments))
        return response

    def expand_comment_branch(self, comment_id, number_of_comments):
        response = self.stub.ExpandCommentBranch(reddit_pb2.ExpandCommentBranchRequest(comment_id=comment_id, number_of_comments=number_of_comments))
        return response

    def monitor_updates(self):
        def request_generator():
            ids_to_monitor = list(self.known_posts) + list(self.known_comments)
            for item_id in ids_to_monitor:
                if (item_id.startswith('post_') and item_id in self.known_posts) or \
                        (item_id.startswith('comment_') and item_id in self.known_comments):
                    if item_id.startswith('post_'):
                        yield reddit_pb2.MonitorUpdatesRequest(post_id=item_id)
                    elif item_id.startswith('comment_'):
                        yield reddit_pb2.MonitorUpdatesRequest(comment_id=item_id)

        try:
            for update in self.stub.MonitorUpdates(request_generator()):
                print(f"Update received for {update.item_id}: New Score is {update.new_score}")
        except grpc.RpcError as e:
            print(f"RPC error occurred: {e.code()}")
            print(e.details())

if __name__ == "__main__":
    client = RedditClient("localhost", 50559)
    client.setup_data()

    client.monitor_updates()  # Start monitoring updates directly
