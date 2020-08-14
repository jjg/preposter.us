# Preposter.us 3 

After several failed attempts at upgrading Preposter.us to Python 3, it became clear that many of the problems are due to using old-fashioned modules to work with email, the html they contain and other things.

Also, I was not a very good Python programmer when I wrote the original code.

So instead, let's start-over.

## The Main Loop

1. Read the config
2. Connect to the mailserver
3. Get the new messages (or all if the "rebuild" option was specified)
4. Process each message
5. Notify the author
6. Notify the administrator of any errors
7. Fin!


## Message Processing

Each message processed will produce some output.  What output is produced will depend on the contents of the message and the modules configured.  These modules include:

* text
* html
* audio 
* video
* podcast
* ???


