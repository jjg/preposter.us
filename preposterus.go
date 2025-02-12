package main

import (
	"fmt"
	"html/template"
	"os"
)

type Config struct {
	ImapServer        string
	SmtpServer        string
	SmtpPort          int
	EmailAddress      string
	EmailPassword     string
	WebHostname       string
	WebFilesystemRoot string
	SysadminEmail     string
}

type Post struct {
	Timestamp string // TODO: Change this to an actual time type
	Title     string
	Body      string
}

func main() {
	fmt.Println("Starting up...")

	/*
		// TODO: Get config dynamically (file, args, etc.)
		c := &Config{
			ImapServer:        "mail.preposter.us",
			SmtpServer:        "mail.preposter.us",
			SmtpPort:          587,
			EmailAddress:      "post@preposter.us",
			EmailPassword:     "nope",
			WebHostname:       "preposter.us",
			WebFilesystemRoot: "www",
			SysadminEmail:     "mr@jasongullickson.com",
		}
	*/

	// TODO: If blog root doesn't exist, create it
	// TODO: Log-in to IMAP server
	// TODO: Get an unread email

	// TODO: Parse an actual email into this post struct
	p := &Post{
		Timestamp: "now-and-shit",
		Title:     "First Post",
		Body:      "Just a long string\n with some line breaks.\n We'll need to handle\n HTML at a later time.\n",
	}

	t := "post.tpl"
	tmpl, err := template.New(t).ParseFiles(t)
	if err != nil {
		panic(err)
	}

	// TODO: Render unique post page
	var f *os.File
	f, err = os.Create("post.html")
	if err != nil {
		panic(err)
	}

	err = tmpl.Execute(f, p)
	if err != nil {
		panic(err)
	}

	err = f.Close()
	if err != nil {
		panic(err)
	}

	// TODO: Update blog index
	//i := []Post

	// TODO: Update blog RSS
	// TODO: Send post status email

	fmt.Println("Finished!")
}
