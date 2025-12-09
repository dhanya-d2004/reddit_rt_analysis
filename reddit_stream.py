import os
import praw
import logging
from praw.exceptions import PRAWException, RedditAPIException
from utils import load_config

logger = logging.getLogger(__name__)

class RedditStreamer:
    def __init__(self):
        """
        Initialize PRAW instance.
        """
        # Ensure config is loaded (env vars)
        load_config()
        
        try:
            self.reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_SECRET"),
                user_agent=os.getenv("USER_AGENT", "python:reddit_ai_analyzer:v1.0 (by /u/unknown)")
            )
            # Verify read-only mode is fine for reading, but credentials are safer
            logger.info(f"Initialized Reddit instance: read_only={self.reddit.read_only}")
            
        except Exception as e:
            logger.error(f"Failed to initialize PRAW: {e}")
            self.reddit = None

    def stream_comments(self, subreddit_name):
        """
        Generator that yields new comments from a subreddit in real-time.
        """
        if not self.reddit:
            logger.error("Reddit instance not initialized.")
            return

        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            logger.info(f"Connecting to r/{subreddit_name} stream...")
            
            # skip_existing=True to only get new comments in real-time
            for comment in subreddit.stream.comments(skip_existing=True):
                try:
                    data = {
                        'id': comment.id,
                        'author': str(comment.author),
                        'body': comment.body,
                        'created_utc': comment.created_utc,
                        'permalink': f"https://reddit.com{comment.permalink}",
                        'subreddit': subreddit_name
                    }
                    yield data
                    
                except AttributeError:
                    # Sometimes deleted comments or quirks
                    continue
                    
        except PRAWException as e:
            logger.error(f"PRAW Error in stream: {e}")
            yield {"error": str(e)}
        except Exception as e:
            logger.error(f"General Error in stream: {e}")
            yield {"error": str(e)}

if __name__ == "__main__":
    # Test stream (requires valid creds in .env)
    print("Testing stream (Ctrl+C to stop)...")
    streamer = RedditStreamer()
    # using 'test' subreddit or popular one for test
    try:
        for comment in streamer.stream_comments("askreddit"):
            print(f"[{comment.get('author')}] {comment.get('body')[:50]}...")
            break # Just one for test
    except KeyboardInterrupt:
        pass
