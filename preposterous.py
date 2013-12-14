#!/usr/bin/python
import imaplib
import email
import os
import hashlib
import smtplib
import sys
import mimetypes
import unicodedata
import re
from email.mime.text import MIMEText

# config
SMTP_SERVER = ''
SMTP_PORT = ''
IMAP_SERVER = ''
IMAP_EMAIL_ADDRESS = ''
IMAP_EMAIL_PASSWORD = ''
WEB_HOST = ''
WEB_ROOT = ''
                
def unpack_message(uid, message, blog_dir):
	email_body = None
	counter = 1
	for part in message.walk():
		if part.get_content_maintype() == 'multipart':
			continue
		filename = part.get_filename()
		if not filename:
			ext = mimetypes.guess_extension(part.get_content_type())
			if not ext:
				# Use a generic bag-of-bits extension
				ext = '.bin'
			filename = 'part-%03d%s' % (counter, ext)
			
		filename = '%s-%s' % (uid, filename)
		
		counter += 1
		
		fp = open(os.path.join(blog_dir, 'assets', filename), 'wb')
		fp.write(part.get_payload(decode=True))
		fp.close()
		
		# extract message body
		if part.get_content_type() == 'text/html':
			email_body = part.get_payload(decode=True)
			
		# append images (this is a hack)
		if filename.find('.jpg') > 0 or filename.find('.png') > 0 or filename.find('.gif') > 0:
			email_body = email_body + '<img src=\'assets/%s\'>' % filename
	
	return email_body

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

# get messages
imap_search = 'UNSEEN'
suppress_notification = False
if len(sys.argv) > 1:
	if sys.argv[1] == 'rebuild':
		imap_search = 'ALL'
		suppress_notification = True
	
mailbox = imaplib.IMAP4_SSL(IMAP_SERVER)
mailbox.login(IMAP_EMAIL_ADDRESS, IMAP_EMAIL_PASSWORD)
mailbox.select()
result, data = mailbox.uid('search', None, imap_search)
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
		
		post_slug = unicodedata.normalize('NFKD', unicode(post_title))
		post_slug = post_slug.encode('ascii', 'ignore').lower()
		post_slug = re.sub(r'[^a-z0-9]+', '-', post_slug).strip('-')
		post_slug = re.sub(r'[-]+', '-', post_slug)
		
		# check for blog subdir
		email_hash = hashlib.md5()
		email_hash.update(email_address)
		blog_directory = email_hash.hexdigest()
		blog_physical_path = WEB_ROOT + '/' + blog_directory
		if not os.path.exists(WEB_ROOT + '/' + blog_directory):
		
			# create directory for new blog
			os.makedirs(blog_physical_path)
			os.makedirs(os.path.join(blog_physical_path, 'assets'))
			
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
			
			if not suppress_notification:
				send_notification(email_address, 'Your new Preposterous blog is ready!', 'You just created a Preposterous blog, a list of your posts can be found here: http://%s/%s .  Find out more about Preposterous by visiting the project repository at https://github.com/jjg/preposterous' % (WEB_HOST, blog_directory))
			
		post_physical_path = blog_physical_path + '/' + post_slug + '.html'
		
		# if necissary, update blog index
		if not os.path.exists(post_physical_path):
			blog_index = open(blog_physical_path + '/index.html', 'a')
			blog_index.write('<li><a href=\'%s.html\'>%s</a> - %s</li>' % (post_slug, post_title, post_date))
			blog_index.close()
	
		# generate post
		post_body = unpack_message(uid, email_message, blog_physical_path)
		post_file = open(post_physical_path, 'w')
		post_file.write('<h3>%s</h3>' % post_title)
		post_file.write(post_body)
		post_file.close()
		
		if not suppress_notification:
			send_notification(email_address, 'Preposterous Post Posted!', 'Your post \"%s\" has been posted, you can view it here: http://%s/%s/%s.html' % (post_title, WEB_HOST, blog_directory, post_slug))