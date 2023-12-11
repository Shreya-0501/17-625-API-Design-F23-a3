from src.main.reddit_grpc.client.client import RedditClient


def retrieve_and_expand_comment(client, post_id):
    """
    Retrieves a post, its top comments, expands the most upvoted comment,
    and returns the most upvoted reply under it.

    :param client: Instance of the API client
    :param post_id: ID of the post
    :return: The most upvoted reply or None
    """

    # Retrieve the post
    post = client.retrieve_post(post_id)
    print(f"Retrieving post with ID {post_id}")

    # Check if the post exists
    if not post:
        print("Post not found.")
        return None
    else:
        print(f"Retrieved post: {post.post.title}, Score: {post.post.score}")

    # Retrieve the top comments of the post
    top_comments = client.retrieve_top_comments(post_id, number_of_comments=1)
    print("Retrieving top comments of the post.")

    # Check if there are any comments
    if not top_comments.comments:
        print("No comments found under the post.")
        return None
    else:
        print(f"Most upvoted comment ID: {top_comments.comments[0].id}, Score: {top_comments.comments[0].score}")

    # Get the most upvoted comment
    most_upvoted_comment = top_comments.comments[0]

    # Expand the most upvoted comment
    expanded_comment = client.expand_comment_branch(most_upvoted_comment.id, number_of_comments=1)
    print(f"Expanding the most upvoted comment with ID: {most_upvoted_comment.id}")

    # Check for replies and return the most upvoted reply
    if expanded_comment.comments and len(expanded_comment.comments) > 1:
        most_upvoted_reply = expanded_comment.comments[1]  # The first comment is the main comment, so the second is the top reply
        print(f"Most upvoted reply ID: {most_upvoted_reply.id}, Text: {most_upvoted_reply.text}, Score: {most_upvoted_reply.score}")
        return most_upvoted_reply
    else:
        print("No replies under the most upvoted comment.")
        return None

def main():

    client = RedditClient("localhost", 50559)

    # Example post ID to be retrieved and expanded
    example_post_id = 'post_1'

    # Call the function
    most_upvoted_reply = retrieve_and_expand_comment(client, example_post_id)

    # Output the result
    if most_upvoted_reply:
        print(f"Most upvoted reply: {most_upvoted_reply.text}")
    else:
        print("No upvoted reply found.")

if __name__ == "__main__":
    main()
