#!/usr/bin/python
import imaplib
import email
import os
import hashlib
import smtplib
from email.mime.text import MIMEText

# config
SMTP_SERVER = ''
SMTP_PORT = ''
IMAP_SERVER = ''
IMAP_EMAIL_ADDRESS = ''
IMAP_EMAIL_PASSWORD = ''
WEB_HOST =''
WEB_ROOT = ''
                
def get_message_html(message):
	message_parts = message.get_payload()
	for part in message_parts:
		if part.get_content_type() == 'text/html':
			return part.get_payload(decode=True)
			
def send_notification(destination_email, subject, message):
	# assemble email
	message = MIMEText(message)
	message['Subject'] = subject
	message['From'] = IMAP_EMAIL_ADDRESS
	message['To'] = destination_email
	
	# send
	s = smtplib.SMTP(SMTP_SERVER + ':' + SMTP_PORT)
	s.ehlo()
	s.starttls()
	s.login(IMAP_EMAIL_ADDRESS, IMAP_EMAIL_PASSWORD)
	s.sendmail(IMAP_EMAIL_ADDRESS, destination_email, message.as_string())
	s.quit()

# check for new messages
mailbox = imaplib.IMAP4_SSL(IMAP_SERVER)
mailbox.login(IMAP_EMAIL_ADDRESS, IMAP_EMAIL_PASSWORD)
mailbox.select()
result, data = mailbox.uid('search', None, 'UNSEEN')
uid_list = data.pop().split(' ')

# if there's no valid uid in the list, skip it
if uid_list[0] != '':
	for uid in uid_list:
		
		# fetch message
		latest_email_uid = uid
		result, data = mailbox.uid('fetch', latest_email_uid, '(RFC822)')
		raw_email = data[0][1]
		email_message = email.message_from_string(raw_email)
		email_from = email.utils.parseaddr(email_message['From'])
		email_address = email_from[1]
		
		# assemble post components
		post_author = email_address.split('@')[0]
		post_date = email_message['Date']
		post_title = email_message['Subject']
		post_slug = post_title.replace(' ', '_')
		post_body = get_message_html(email_message)
		
		# check for blog subdir
		email_hash = hashlib.md5()
		email_hash.update(email_address)
		blog_directory = email_hash.hexdigest()
		blog_physical_path = WEB_ROOT + '/' + blog_directory
		if not os.path.exists(WEB_ROOT + '/' + blog_directory):
		
			# create directory for new blog
			os.makedirs(blog_physical_path)
			
			# create the blog index
			blog_index = open(blog_physical_path + '/index.html', 'a')
			blog_index.write('<html><head><title>preposterous blog of %s</title></head>' % post_author)
			blog_index.write('<body><h1>%s\'s preposterous blog</h1>' % post_author)
			blog_index.write('<h3>Posts</h3>\n<ul>')
			blog_index.close()
			
			# update site index
			site_index = open(WEB_ROOT + '/index.html', 'a')
			site_index.write('<li><a href=\'%s\'>%s</a></li>\n' % (blog_directory, post_author))
			site_index.close()
			
			send_notification(email_address, 'Your new Preposterous blog is ready!', 'You just created a Preposterous blog, a list of your posts can be found here: http://%s/%s .  Find out more about Preposterous by visiting the project repository at https://github.com/jjg/preposterous' % (WEB_HOST, blog_directory))
			
		post_physical_path = blog_physical_path + '/' + post_slug + '.html'
		
		# if necissary, update blog index
		if not os.path.exists(post_physical_path):
			blog_index = open(blog_physical_path + '/index.html', 'a')
			blog_index.write('<li><a href=\'%s.html\'>%s</a> - %s</li>' % (post_slug, post_title, post_date))
			blog_index.close()
	
		# generate post
		post_file = open(post_physical_path, 'w')
		post_file.write('<h3>%s</h3>' % post_title)
		post_file.write(post_body)
		post_file.close()
		
		send_notification(email_address, 'Preposterous Post Posted!', 'Your post \"%s\" has been posted, you can view it here: http://%s/%s/%s.html' % (post_title, WEB_HOST, blog_directory, post_slug))