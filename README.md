This is a python script using PRAW to monitor a subreddit's modmail for flair requests.  Useful for subs that may have flairs that require verification for whatever reason.  We use it on /r/BJJ to streamline verification for black belts.

This does require that you register your own bot account with reddit and get a client ID and secret to authenticate with the API.  That information will go in your secrets.py file.

Just install Python on whatever computer, server, VPS, or whatever you're using and run 'pip install praw' to install the necessary stuff to talk to the reddit API.  Swap out the placeholders in the script, run the script.  Easy.

Future versions may or may not include (depending on how motivated I am) parsing the mod response for a custom flair to set, maybe scouring posts/comments for things that look like requests.
