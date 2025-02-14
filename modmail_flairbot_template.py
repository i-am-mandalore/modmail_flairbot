import praw
import time
import os
import secrets
import re
# Using a flat file instead of replit database
PROCESSED_CONVERSATIONS_FILE = "processed_conversations.txt"

# Reddit API credentials
REDDIT_USER_AGENT = "modmail_flairbot by /u/iammandalore"
client_id = secrets.client_id # This is the client ID given to you by reddit for your bot account
client_secret = secrets.client_secret # Client secret for your bot account
username = secrets.username # Username for your bot account
password = secrets.password # Password for your bot account

# Subreddit to monitor and flair to set
SUBREDDIT_NAME = "your_sub_with_no_r"
FLAIR_TEXT = "WhAtEveR"

# Authenticate with Reddit
reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    username=username,
    password=password,
    user_agent=REDDIT_USER_AGENT
)

# Function to grab a list of active conversations from our flat file
def get_processed_conversations():
    try:
        with open(PROCESSED_CONVERSATIONS_FILE, "r") as file:
            return dict(line.strip().split(":", 1) for line in file if ":" in line)
    except FileNotFoundError:
        return {}

# Function to add a conversation to our list
def add_processed_conversation(conversation_id, username):
    with open(PROCESSED_CONVERSATIONS_FILE, "a") as file:
        file.write(f"{conversation_id}:{username}\n")

# Function to delete a conversation from our list
def remove_processed_conversation(conversation_id):
    conversations = get_processed_conversations()
    if conversation_id in conversations:
        del conversations[conversation_id]
        with open(PROCESSED_CONVERSATIONS_FILE, "w") as file:
            for cid, uname in conversations.items():
                file.write(f"{cid}:{uname}\n")

# Our main monitoring function
def monitor_modmail():
    while True:
        for state in ["new", "inprogress"]: # Checking modmail messages that are either new or in progress to avoid reading anything archived
            for conversation in reddit.subreddit(SUBREDDIT_NAME).modmail.conversations(state=state):
                SUBJECT_TEXT = conversation.subject # Grabbing the subject of a conversation
                if any(keyword in SUBJECT_TEXT.casefold() for keyword in ["words", "go", "here"]) and conversation.id not in get_processed_conversations() and not any(keyword in message.body for message in conversation.messages for keyword in ["I've changed your flair", "neighborhood FlairBot"]): # Looking for any messages in the correct state which contain keywords we want to watch for, but avoiding anything that may have already been responded to by the bot
                    user = conversation.participant # Setting the user variable to the username of the redditor who started the modmail thread
                    if user:
                        add_processed_conversation(conversation.id, user.name)

                        # Check if the message contains URLs
                        message_body = ''.join(message.body for message in conversation.messages if message.author == conversation.participant)
                        urls = re.findall(r'https?://\S+', message_body)

                        if not urls:
                            # Remind the user about requirements if no URLs are found
                            conversation.reply(body="This is your friendly neighborhood FlairBot. It looks like you're asking about having your flair updated. I don't see any links in your message.  Please check here for verification requirements: https://www.reddit.com/r/your_sub_here/wiki/wiki_article \n\n Once you send us the requested info a moderator will review your request and get back with you. \n\n If you're not here to request that your flair be changed, just tell me to 'go home'.", author_hidden=False)
                        else:
                            # If a URL is present we tell the user we'll review
                            conversation.reply(body="This is your friendly neighborhood FlairBot. It looks like you're asking about having your flair updated. I see a link in your message. A moderator will review your request and get back with you. \n\n If you're not here to request that your flair be changed, just tell me to 'go home'.", author_hidden=False)
                        print(f"Flair request received from {user.name}")

                # Check for mod approval
                if conversation.id in get_processed_conversations() and not any("I've changed your flair" in message.body for message in conversation.messages):
                    latest_message = conversation.messages[-1]
                    notbot_body = ''.join(message.body for message in conversation.messages if message.author != "your_bot_username") # Compiling one big block of text to search that doesn't include messages from the bot
                    if any(phrase in notbot_body.casefold() for phrase in ["you're drunk flairbot", "you're drunk, flairbot", "go home"]): # Check for one of these phrases to tell the bot to ignore the conversation.
                        conversation.reply(body="Ope, sorry. I'll leave you guys to it then.", author_hidden=False)
                        print(f"Bot exiting and conversation {conversation.id} deleted from local DB.")
                        remove_processed_conversation(conversation.id)
                    if any(phrase in notbot_body.casefold() for phrase in ["no bb", "disapproved", "you should feel bad"]): # Check for one of these phrases to have the bot tell the user off.
                        conversation.reply(body="Big bad mod-man says no flair for u, bb.  Skill issue TBH.", author_hidden=False)
                        print(f"Flair denied in conversation {conversation.id}.  Conversation deleted.")
                        remove_processed_conversation(conversation.id)
                        continue  
                    if latest_message.author.is_mod and "congrats" in latest_message.body.casefold(): # Checking for 'congrats' or whatever keyword you want to put here
                        user_to_flair = get_processed_conversations().get(conversation.id, None)
                        reddit.subreddit(SUBREDDIT_NAME).flair.set(user_to_flair, text=FLAIR_TEXT) # Actually setting the flair
                        print(f"Flair updated for {user_to_flair}.  Exiting and archiving conversation {conversation.id}.")

                        # Send a response to the user
                        conversation.reply(body="This is your friendly neighborhood FlairBot. I've updated your flair. This message thread is going to be archived now, but if you find that your flair did not update correctly, please respond back and let us know.  Otherwise, congrats!\n\nPlease do us a solid and don't respond to this message.  If you wanted to say thanks, then you're welcome! :)  But if you respond to this message it might confuse our bot.  He's hard-working and earnest, but he's also a simple little guy.", author_hidden=False)

                        conversation.archive()  # Mark as archived
                        remove_processed_conversation(conversation.id) # Delete conversation from the list because we're done with it

        time.sleep(60)  # Check modmail every 60 seconds

if __name__ == "__main__":
    monitor_modmail()
