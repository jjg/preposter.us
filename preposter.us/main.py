import logging
from imaplib import IMAP4_SSL
import email

import config

logging.basicConfig(level=logging.DEBUG)

def main():
    
    # Connect to mailserver
    logging.info("Connecting to mailserver")
    with IMAP4_SSL(config.IMAP_SERVER) as imap_server:

        logging.info("Logging-in")
        login_result, login_data = imap_server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)

        logging.info(f"Login result: {login_result}")

        # Get messages
        logging.info("Getting messages")
        select_result, select_data = imap_server.select()
        logging.info(f"Select result: {select_result}")

        # TODO: Change "ALL" to "UNSEEN" so only new emails are processed
        search_result, search_data = imap_server.search(None, "ALL")
        logging.info(f"Search result: {search_result}, ({len(search_data)} messages)")

        for message_number in search_data[0].split():

            logging.debug(f"Message number: {message_number}")

            fetch_result, fetch_data = imap_server.fetch(message_number, "RFC822")
            logging.info(f"Fetch result: {fetch_result}")

            message = email.message_from_bytes(fetch_data[0][1])
            logging.debug(f"Message keys: {message.keys()}")
            logging.info(f"From: {message['From']}")
            logging.info(f"Subject: {message['Subject']}")
            logging.info(f"Date: {message['Date']}")

            # TODO: Process message
            logging.info("Processing message")

            # TODO: Update blog
            logging.info("Updating blog")

            # TODO: Notify author
            logging.info("Notifying author")


if __name__ == "__main__":
    
    main()
