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
import ConfigParser
import shutil
import traceback
import humanhash
import json
import xml.etree.ElementTree as ET
#import dateutil
from email.mime.text import MIMEText

# load config
config = ConfigParser.RawConfigParser()
config.read('preposter.us.cfg')

IMAP_SERVER = config.get('mailserver', 'imap_server')
SMTP_SERVER = config.get('mailserver', 'smtp_server')
SMTP_PORT = config.get('mailserver', 'smtp_port')
EMAIL_ADDRESS = config.get('mailserver', 'email_address')
EMAIL_PASSWORD = config.get('mailserver', 'email_password')
WEB_HOST = config.get('webserver', 'web_hostname')
WEB_ROOT = config.get('webserver', 'web_filesystem_root')
ADMIN_EMAIL = config.get('system', 'admin_email')
        
class Post(object):
    title = ''
    slug = ''
    author = ''
    date = ''
    url = ''

    def __iter__(self):
        yield 'title', self.title
        yield 'slug', self.slug
        yield 'author', self.author
        yield 'date', self.date
        yield 'url', self.url

def unpack_message(uid, message, blog_dir):
    email_body = ''
    html_body = ''
    text_body = ''
    counter = 1
    audio_filename = None
    audio_length = 0
    
    for part in message.walk():
        
        if part.get_content_maintype() == 'multipart':
            continue

        # extract message body
        if part.get_content_type() == 'text/html':
            # TODO: remove any containing head/body tags
            html_body = part.get_payload(decode=True)
            
        if part.get_content_type() == 'text/plain':
            text_body += part.get_payload(decode=True)
            
        filename = part.get_filename()
        if not filename:
            ext = mimetypes.guess_extension(part.get_content_type())
            if not ext:
                # Use a generic bag-of-bits extension
                ext = '.bin'
            filename = 'part-%03d%s' % (counter, ext)
            
        filename = '%s-%s' % (uid, filename)
        
        # only store files we know what to do with
        store_file = False
        
        # caps just makes comparisons harder
        filename = filename.lower()
        
        # handle images
        if filename.find('.jpg') > 0 or filename.find('.jpeg') > 0 or filename.find('.png') > 0 or filename.find('.gif') > 0 or filename.find('.pdf') > 0:
            store_file = True
            
            if part.get('Content-ID'):
                cid = 'cid:%s' % part.get('Content-ID')[1:-1]
                # if we can find the file embedded, update the link
                if html_body.find(cid) > -1:
                    # re-write CID img tag to use stored filename
                    html_body = html_body.replace(cid, 'assets/%s' % filename)
            else:
                # otherwise, just embed the file
                email_body = email_body + '<a href=\'assets/%s\'><img src=\'assets/%s\'></a>' % (filename, filename)
            
        # handle video
        if filename.find('.mov') > 0 or filename.find('.mp4') > 0 or filename.find('.ogg') > 0 :
            store_file = True
            email_body = email_body + '<video controls><source src=\'assets/%s\'></video>' % filename
        
        # handle audio
        if filename.find('.mp3') > 0 or filename.find('.wav') > 0 or filename.find('.m4a') > 0:
            store_file = True
            email_body = email_body + '<audio controls><source src=\'assets/%s\'></audio>' % filename
            audio_filename = filename
            
            # There might be a better way to get this number...
            audio_length = len(part.get_payload(decode=True))
        
        if store_file:
            counter += 1
            fp = open(os.path.join(blog_dir, 'assets', filename), 'wb')
            fp.write(part.get_payload(decode=True))
            fp.close()
    
    if html_body:
        email_body = html_body + email_body
    else:
        email_body = text_body + email_body

    return {"email_body": email_body, "audio_filename": audio_filename, "audio_length": audio_length}

def send_notification(destination_email, subject, message):
    # assemble email
    message = MIMEText(message)
    message['Subject'] = subject
    message['From'] = EMAIL_ADDRESS
    message['To'] = destination_email
    
    # send
    s = smtplib.SMTP(SMTP_SERVER + ':' + SMTP_PORT)
    s.ehlo()
    s.starttls()
    s.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    s.sendmail(EMAIL_ADDRESS, destination_email, message.as_string())
    s.quit()

# get messages
imap_search = 'UNSEEN'
suppress_notification = False
if len(sys.argv) > 1:
    if sys.argv[1] == 'rebuild':
        shutil.copy('index.html', WEB_ROOT)
        shutil.copy('podcast.xml', WEB_ROOT)
        shutil.copytree('images', WEB_ROOT + '/images')
        shutil.copytree('css', WEB_ROOT + '/css')
        imap_search = 'ALL'
        suppress_notification = True
    
mailbox = imaplib.IMAP4_SSL(IMAP_SERVER)
mailbox.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
mailbox.select()
result, data = mailbox.uid('search', None, imap_search)
uid_list = data.pop().split(' ')

# if there's no valid uid in the list, skip it
if uid_list[0] != '':
    for uid in uid_list:
    
        # global exception handlers like this are for bad programmers
        try:
        
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
            humane_blog_name = humanhash.humanize(blog_directory)
            if not os.path.exists(WEB_ROOT + '/' + blog_directory):
            
                # create directory for new blog
                os.makedirs(blog_physical_path)
                os.makedirs(os.path.join(blog_physical_path, 'assets'))
            
                # copy over the default stylsheet
                shutil.copytree('css', blog_physical_path + '/css')
    
                # create human-readable link to blog directory
                os.symlink(blog_directory, os.path.join(WEB_ROOT, humane_blog_name))
                
                # create html blog post index
                template = open('postindextemplate.html', 'r').read()
                new_index = template
                new_index = new_index.replace('{0}', post_author)
                new_index = new_index.replace('{1}', blog_directory)
                
                blog_index = open(blog_physical_path + '/index.html', 'w')
                blog_index.write(new_index)
                blog_index.close()
                
                # create rss blog post index
                template = open('postrssindextemplate.xml', 'r').read()
                new_index = template
                new_index = new_index.replace('{0}', '%s\'s Preposter.us Blog' % post_author)
                new_index = new_index.replace('{1}', 'http://%s/%s' % (WEB_HOST, humane_blog_name))
                new_index = new_index.replace('{2}', '%s\'s blog on preposter.us' % post_author)
                
                blog_index = open(blog_physical_path + '/rss.xml', 'w')
                blog_index.write(new_index)
                blog_index.close()
                
                # podcast support - create individual podcast XML
                template = open('podcastrssindextemplate.xml', 'r').read()
                new_index = template
                new_index = new_index.replace('{0}', '%s\'s Preposter.us Podcast' % post_author)
                new_index = new_index.replace('{1}', 'http://%s/%s' % (WEB_HOST, humane_blog_name))
                new_index = new_index.replace('{2}', '%s\'s podcast on preposter.us' % post_author)
                
                blog_index = open(blog_physical_path + '/podcast.xml', 'w')
                blog_index.write(new_index)
                blog_index.close()
                
                # add new blog to site index
                blog_index_partial = open(WEB_ROOT + '/blogs.html', 'a')
                blog_index_partial.write('<li><a href=\'%s\'>%s</a></li>\n' % (humane_blog_name, post_author))
                blog_index_partial.close()
                
                if not suppress_notification:
                    send_notification(email_address, 'Your new Preposter.us blog is ready!', 'You just created a Preposter.us blog, a list of your posts can be found here: http://%s/%s .  Find out more about Preposter.us by visiting the project repository at https://github.com/jjg/preposter.us' % (WEB_HOST, humane_blog_name))
                
            post_physical_path = blog_physical_path + '/' + post_slug + '.html'
            
            # parse the actual message
            unpacked_message = unpack_message(uid, email_message, blog_physical_path)
            post_body = unpacked_message["email_body"]
            
            # if necessary, update post index
            if not os.path.exists(post_physical_path):
                
                # update post index partial
                post_index_partial = open(blog_physical_path + '/posts.html', 'a')
                post_index_partial.write('<li><a href=\'%s.html\'>%s</a> - %s</li>' % (post_slug, post_title, post_date))
                post_index_partial.close()
                
                # update post index json
                post = Post()
                post.title = post_title
                post.slug = post_slug
                post.author = post_author
                post.date = post_date
                post.url = 'http://' + WEB_HOST + '/' + humane_blog_name + '/' + post_slug + '.html'
                
                # create a new index or update an existing one
                json_index_physical_path = blog_physical_path + '/posts.json'
                post_index_obj = {'posts':[]}
                if os.path.exists(json_index_physical_path):
                    post_index_json = open(json_index_physical_path, 'r')
                    post_index_obj = json.loads(post_index_json.read())
                    post_index_json.close()
                
                post_index_obj['posts'].append({'post':dict(post)})
                post_index_json = open(json_index_physical_path, 'w')
                post_index_json.write(json.dumps(post_index_obj))
                post_index_json.close()
                
                # update rss feed
                rss_physical_path = blog_physical_path + '/rss.xml'
                tree = ET.parse(rss_physical_path)
                root = tree.getroot()
                
                # add new post
                channel = root.find('channel')
                item = ET.SubElement(channel, 'item')
                item_title = ET.SubElement(item, 'title')
                item_link = ET.SubElement(item, 'link')
                item_guid = ET.SubElement(item, 'guid')
                item_pub_date = ET.SubElement(item, 'pubDate')
                item_description = ET.SubElement(item, 'description')
                
                item_title.text = post.title
                item_link.text = post.url
                item_guid.text = post.url
                item_pub_date.text = post.date
                item_description.text = 'a post about %s by %s' % (post.title, post.author)
                
                # save changes
                tree.write(rss_physical_path)
                
                # podcast support - add post to podcast XML if media is present
                if unpacked_message["audio_filename"]:
                    
                    # unpack media attributes
                    audio_filename = unpacked_message["audio_filename"]
                    audio_length = str(unpacked_message["audio_length"])
                    audio_type = "audio/%s" % audio_filename.split(".")[-1]
                    audio_url = "http://%s/%s/assets/%s" % (WEB_HOST, humane_blog_name, audio_filename)
                    
                    # update user's podcast
                    podcast_physical_path = blog_physical_path + '/podcast.xml'
                    tree = ET.parse(podcast_physical_path)
                    root = tree.getroot()
                    
                    # add new episode
                    channel = root.find('channel')
                    item = ET.SubElement(channel, 'item')
                    item_title = ET.SubElement(item, 'title')
                    item_link = ET.SubElement(item, 'link')
                    item_guid = ET.SubElement(item, 'guid')
                    item_pub_date = ET.SubElement(item, 'pubDate')
                    item_description = ET.SubElement(item, 'description')
                    item_enclosure = ET.SubElement(item, 'enclosure')
                    
                    item_title.text = post.title
                    item_link.text = post.url
                    item_guid.text = post.url
                    item_pub_date.text = post.date
                    item_description.text = 'an episode about %s by %s' % (post.title, post.author)
                    
                    # TODO: add extended podcast attributes
                    
                    item_enclosure.set("url", audio_url)
                    item_enclosure.set("type", audio_type) 
                    item_enclosure.set("length", audio_length)
                    
                    # save changes
                    tree.write(podcast_physical_path)
                    
                    # update site-wide podcast
                    # TODO: this could be DRY'd up
                    podcast_physical_path = WEB_ROOT + '/podcast.xml'
                    tree = ET.parse(podcast_physical_path)
                    root = tree.getroot()
                    
                    # add new episode
                    channel = root.find('channel')
                    item = ET.SubElement(channel, 'item')
                    item_title = ET.SubElement(item, 'title')
                    item_link = ET.SubElement(item, 'link')
                    item_guid = ET.SubElement(item, 'guid')
                    item_pub_date = ET.SubElement(item, 'pubDate')
                    item_description = ET.SubElement(item, 'description')
                    item_enclosure = ET.SubElement(item, 'enclosure')
                    
                    item_title.text = post.title
                    item_link.text = post.url
                    item_guid.text = post.url
                    item_pub_date.text = post.date
                    item_description.text = 'an episode about %s by %s' % (post.title, post.author)
                    
                    # TODO: add extended podcast attributes
                    
                    item_enclosure.set("url", audio_url)
                    item_enclosure.set("type", audio_type) 
                    item_enclosure.set("length", audio_length)
                    
                    # save changes
                    tree.write(podcast_physical_path)                    
                
            # write post to disk
            post_template = open('posttemplate.html', 'r').read()
            new_post = post_template
            new_post = new_post.replace('{0}', post_title)
            new_post = new_post.replace('{1}', post_author)
            new_post = new_post.replace('{2}', post_body)
            # TODO: format this date to something prettier
            new_post = new_post.replace('{3}', post_date)
            
            post_file = open(post_physical_path, 'w')
            post_file.write(new_post)
            post_file.close()
            
            if not suppress_notification:
                send_notification(email_address, 'Preposter.us Post Posted!', 'Your post \"%s\" has been posted, you can view it here: http://%s/%s/%s.html' % (post_title, WEB_HOST, humane_blog_name, post_slug))
                
        except:
            print '****************************************'
            print traceback.format_exc()
            print raw_email
            print '****************************************'
