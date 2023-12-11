import argparse
from concurrent import futures
import grpc
import reddit_pb2
import reddit_pb2_grpc

class RedditService(reddit_pb2_grpc.RedditServiceServicer):
    """
    Implements the RedditService gRPC service, providing functionalities
    similar to a simplified version of Reddit.
    """
    def __init__(self):
        """
        Implements the RedditService gRPC service, providing functionalities
        similar to a simplified version of Reddit.
        """
        self.posts = {}
        self.comments = {}
        self.posts_and_comments = {}
        self.subreddits = {}
        self.next_post_id = 1
        self.next_comment_id = 1
        self.setup_data()

    def setup_data(self):
        """
        Initializes the RedditService with empty data structures for posts,
        comments, and related entities.
        """
        for post_id, post in self.posts.items():
            self.posts_and_comments[post_id] = post.score
        for comment_id, comment in self.comments.items():
            self.posts_and_comments[comment_id] = comment.score

        # Creating dummy posts
        for i in range(1, 5):
            post_id = f'post_{i}'
            post = reddit_pb2.Post(id=post_id, title=f"Sample Post {i}", text=f"Content of post {i}", score=i*10, author=f"author{i}")
            self.posts[post_id] = post

        # Creating dummy comments
        for i in range(1, 10):
            comment_id = f'comment_{i}'
            parent_id = f'post_{(i % 4) + 1}'  # Associate comments with posts in a round-robin fashion
            comment = reddit_pb2.Comment(id=comment_id, text=f"Sample comment {i}", score=i*5, parent_id=parent_id)
            self.comments[comment_id] = comment

            # Link comments to their respective posts
            self.posts[parent_id].comment_ids.append(comment_id)

            # Creating nested comments for the first two comments
            if i <= 2:
                for j in range(1, 3):  # Two replies per comment
                    nested_comment_id = f'comment_{i}_{j}'
                    nested_comment = reddit_pb2.Comment(id=nested_comment_id, text=f"Nested comment {i}-{j}", score=j*3, parent_id=comment_id)
                    self.comments[nested_comment_id] = nested_comment
                    comment.reply_ids.append(nested_comment_id)

    def calculate_new_score(self, item_id):
        """
        Calculates and updates the new score for a post or comment.
        Args:
            item_id: ID of the post or comment.
        Returns:
            The new score after incrementing.
        """
        self.posts_and_comments[item_id] += 1
        return self.posts_and_comments[item_id]

    def get_next_post_id(self):
        """
        Generates the next post ID.
        Returns:
            A string representing the next post ID.
        """
        post_id = f'post_{self.next_post_id}'
        self.next_post_id += 1
        return post_id

    def get_next_comment_id(self):
        """
        Generates the next comment ID.
        Returns:
            A string representing the next comment ID.
        """
        comment_id = f'comment_{self.next_comment_id}'
        self.next_comment_id += 1
        return comment_id

    def CreatePost(self, request, context):
        """
        Creates a new post with given details.
        Args:
            request: An instance of CreatePostRequest containing the post details.
            context: gRPC context.
        Returns:
            A CreatePostResponse containing the newly created post.
        """
        post_id = self.get_next_post_id()
        post = request.post
        post.id = post_id
        post.score = 0
        self.posts[post_id] = post
        return reddit_pb2.CreatePostResponse(post=post)

    def VotePost(self, request, context):
        """
        Handles voting (upvote/downvote) for a post.
        Args:
            request: An instance of VotePostRequest containing the post ID and vote type.
            context: gRPC context.
        Returns:
            A VotePostResponse containing the new score of the post.
        """
        post = self.posts.get(request.post_id)
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, 'Post not found')
        post.score += 1 if request.upvote else -1
        self.posts_and_comments[request.post_id] = post.score
        return reddit_pb2.VotePostResponse(new_score=post.score)

    def RetrievePost(self, request, context):
        """
        Retrieves a post based on the provided post ID.
        Args:
            request: An instance of RetrievePostRequest containing the post ID.
            context: gRPC context.
        Returns:
            A RetrievePostResponse containing the post details.
        """
        post = self.posts.get(request.post_id)
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, 'Post not found')
        return reddit_pb2.RetrievePostResponse(post=post)

    def CreateComment(self, request, context):
        """
        Creates a new comment for a post or another comment.
        Args:
            request: An instance of CreateCommentRequest containing the comment details.
            context: gRPC context.
        Returns:
            A CreateCommentResponse containing the newly created comment.
        """
        try:
            comment_id = self.get_next_comment_id()
            comment = request.comment
            comment.id = comment_id
            comment.score = 0

            parent_id = comment.parent_id
            if parent_id.startswith('post_') and parent_id in self.posts:
                self.posts[parent_id].comment_ids.append(comment_id)
            elif parent_id.startswith('comment_') and parent_id in self.comments:
                self.comments[parent_id].reply_ids.append(comment_id)
                self.comments[parent_id].has_replies = True

            else:
                context.abort(grpc.StatusCode.NOT_FOUND, 'Parent post or comment not found')

        except Exception as e:
            print(f"Exception in CreateComment: {e}")
            raise

        self.comments[comment_id] = comment
        return reddit_pb2.CreateCommentResponse(comment=comment)

    def VoteComment(self, request, context):
        """
        Handles voting (upvote/downvote) for a comment.
        Args:
            request: An instance of VoteCommentRequest containing the comment ID and vote type.
            context: gRPC context.
        Returns:
            A VoteCommentResponse containing the new score of the comment.
        """
        comment = self.comments.get(request.comment_id)
        if not comment:
            context.abort(grpc.StatusCode.NOT_FOUND, 'Comment not found')
        comment.score += 1 if request.upvote else -1
        self.posts_and_comments[request.comment_id] = comment.score
        return reddit_pb2.VoteCommentResponse(new_score=comment.score)

    def RetrieveTopComments(self, request, context):
        """
        Retrieves the top comments of a post.
        Args:
            request: An instance of RetrieveTopCommentsRequest containing the post ID and number of comments to retrieve.
            context: gRPC context.
        Returns:
            A RetrieveTopCommentsResponse containing the top comments of the post.
        """
        # Find the post and its associated comments
        post = self.posts.get(request.post_id)
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, 'Post not found')

        # Retrieve the comments for the post
        comments_list = [self.comments[c_id] for c_id in post.comment_ids if c_id in self.comments]

        # Sort comments by score and take the top N
        top_comments = sorted(comments_list, key=lambda c: c.score, reverse=True)[:request.number_of_comments]
        for comment in top_comments:
            comment.has_replies = bool(self.comments[comment.id].reply_ids)  # Check if the comment has any replies

        return reddit_pb2.RetrieveTopCommentsResponse(comments=top_comments)


    def ExpandCommentBranch(self, request, context):
        """
        Expands a comment branch to retrieve its replies.
        Args:
            request: An instance of ExpandCommentBranchRequest containing the comment ID and number of replies to retrieve.
            context: gRPC context.
        Returns:
            An ExpandCommentBranchResponse containing the comment and its replies.
        """
        main_comment = self.comments.get(request.comment_id)
        if not main_comment:
            context.abort(grpc.StatusCode.NOT_FOUND, 'Comment not found')

        replies = [self.comments[reply_id] for reply_id in main_comment.reply_ids][:request.number_of_comments]
        return reddit_pb2.ExpandCommentBranchResponse(comments=[main_comment] + replies)

    def MonitorUpdates(self, request_iterator, context):
        """
        Monitors updates to posts and comments and streams the updated scores.
        Args:
            request_iterator: An iterator over MonitorUpdatesRequest objects.
            context: gRPC context.
        Yields:
            MonitorUpdatesResponse objects containing updated scores for monitored items.
        """
        for request in request_iterator:
            item_id = request.post_id or request.comment_id
            print(f"Monitoring request received for: {item_id}")  # Debugging line
            if item_id in self.posts_and_comments:
                updated_score = self.calculate_new_score(item_id)  # Implement this method
                yield reddit_pb2.MonitorUpdatesResponse(item_id=item_id, new_score=updated_score)
            else:
                print(f"Item not found: {item_id}")  # Debugging line
                context.abort(grpc.StatusCode.NOT_FOUND, f'{item_id} not found')

def serve(host, port):
    """
    Starts the gRPC server with the RedditService.
    Args:
        host: The hostname to listen on.
        port: The port number to listen on.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    reddit_pb2_grpc.add_RedditServiceServicer_to_server(RedditService(), server)
    server.add_insecure_port(f'{host}:{port}')
    server.start()
    print(f"Server started at {host}:{port}")
    server.wait_for_termination()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Reddit gRPC Server')
    parser.add_argument('--host', type=str, default='localhost', help='Host to serve on')
    parser.add_argument('--port', type=int, default=5555, help='Port to serve on')
    args = parser.parse_args()

    serve(args.host, args.port)
