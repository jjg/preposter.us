#!/usr/bin/python

# preposterous
# preposterous1984@gmail.com !1a2S3d4f5g!

import imaplib
import email
import os


def get_first_text_block(email_message_instance):
    maintype = email_message_instance.get_content_maintype()
    if maintype == 'multipart':
        for part in email_message_instance.get_payload():
            if part.get_content_maintype() == 'text':
                return part.get_payload()
    elif maintype == 'text':
        return email_message_instance.get_payload()


# check for new messages
mailbox = imaplib.IMAP4_SSL('imap.gmail.com')
mailbox.login('preposterous1984@gmail.com', '!1a2S3d4f5g!')
mailbox.select()
result, data = mailbox.uid('search', None, "ALL")
uid_list = data.pop().split(' ')

print('processing %d messages\n' % len(uid_list))

for uid in uid_list:
	
	# fetch message
	latest_email_uid = uid
	result, data = mailbox.uid('fetch', latest_email_uid, '(RFC822)')
	raw_email = data[0][1]
	email_message = email.message_from_string(raw_email)
	email_from = email.utils.parseaddr(email_message['From'])
	email_address = email_from[1]
	
	# assemble post components
	post_title = email_message['Subject'].replace(' ', '_')
	post_body = get_first_text_block(email_message).replace('\n', '</br>')
	
	# check for sender subdir
	if not os.path.exists(email_address):
	
		# create directory for new blog
		os.makedirs(email_address)
		
		# update site index
		site_index = open('index.html', 'a')
		site_index.write('<a href=\'%s\'>%s</a></br>' % (email_address, email_address))
		site_index.close()
	
	# generate post
	post_file = open(email_address + '/' + post_title + '.html', 'w')
	post_file.write(post_body)
	post_file.close()
	
	# update blog index
	blog_index = open(email_address + '/index.html', 'a')
	blog_index.write('<a href=\'%s.html\'>%s</a></br>' % (post_title, post_title))
	blog_index.close()



