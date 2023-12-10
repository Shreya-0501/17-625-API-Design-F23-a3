import argparse
import time

import grpc
from concurrent import futures
import reddit_pb2
import reddit_pb2_grpc


class RedditService(reddit_pb2_grpc.RedditServiceServicer):
    def __init__(self):
        self.posts = {}
        self.comments = {}
        self.posts_and_comments = {}
        self.subreddits = {}
        self.next_post_id = 1
        self.next_comment_id = 1

    def get_next_post_id(self):
        post_id = self.next_post_id
        self.next_post_id += 1
        return f'post{post_id}'

    def get_next_comment_id(self):
        comment_id = self.next_comment_id
        self.next_comment_id += 1
        return f'comment{comment_id}'

    def CreatePost(self, request, context):
        post_id = self.get_next_post_id()
        post = request.post
        post.score = 0  # Initialize score
        post.id = post_id
        self.posts[post_id] = post
        return reddit_pb2.PostResponse(post=post)

    def VotePost(self, request, context):
        post = self.posts.get(request.post_id)
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, 'Post not found')
        post.score += 1 if request.upvote else -1
        return reddit_pb2.VoteResponse(new_score=post.score)

    def RetrievePost(self, request, context):
        post = self.posts.get(request.post_id)
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, 'Post not found')
        return reddit_pb2.PostResponse(post=post)

    def CreateComment(self, request, context):
        comment_id = self.get_next_comment_id()
        comment = request.comment
        comment.id = comment_id
        comment.score = 0  # Initialize score
        self.comments[comment_id] = comment
        return reddit_pb2.CommentResponse(comment=comment)

    def VoteComment(self, request, context):
        comment = self.comments.get(request.comment_id)
        if not comment:
            context.abort(grpc.StatusCode.NOT_FOUND, 'Comment not found')
        comment.score += 1 if request.upvote else -1
        return reddit_pb2.VoteResponse(new_score=comment.score)

    def RetrieveTopComments(self, request, context):
        top_comments = sorted(self.comments.values(), key=lambda c: c.score, reverse=True)[:request.number_of_comments]
        return reddit_pb2.TopCommentsResponse(comments=top_comments)

    def ExpandCommentBranch(self, request, context):
        main_comment = self.comments.get(request.comment_id)
        if not main_comment:
            context.abort(grpc.StatusCode.NOT_FOUND, 'Comment not found')
        replies = [self.comments[c_id] for c_id in main_comment.replies][:request.number_of_comments]
        return reddit_pb2.CommentBranchResponse(comments=[main_comment] + replies)

    def MonitorUpdates(self, request_iterator, context):
        for request in request_iterator:
            print(f"Received request: {request}")
            if request.HasField('post_id'):
                post_id = request.post_id
                if post_id in self.posts:
                    self.posts_and_comments[post_id] = self.posts[post_id].score
                else:
                    context.abort(grpc.StatusCode.NOT_FOUND, 'Post not found')
            elif request.HasField('comment_id'):
                comment_id = request.comment_id
                if comment_id in self.comments:
                    self.posts_and_comments[comment_id] = self.comments[comment_id].score
                else:
                    # Skip if comment not found, or handle it differently
                    continue

            # Increment scores and send updates
            for item_id in list(self.posts_and_comments.keys()):
                self.posts_and_comments[item_id] += 1
                yield reddit_pb2.ScoreUpdateResponse(item_id=item_id, new_score=self.posts_and_comments[item_id])
                time.sleep(1)

def serve(host, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    reddit_pb2_grpc.add_RedditServiceServicer_to_server(RedditService(), server)
    server.add_insecure_port(f'{host}:{port}')
    server.start()
    print(f"Server started at {host}:{port}")
    server.wait_for_termination()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Reddit gRPC Server')
    parser.add_argument('--host', type=str, default='localhost', help='Host to serve on')
    parser.add_argument('--port', type=int, default=50051, help='Port to serve on')
    args = parser.parse_args()

    serve(args.host, args.port)
