package main

import (
	"fmt"
	"github.com/BrianLeishman/go-imap"
	"time"
)

type Post struct {
	Title  string
	Author string
	Posted time.Time
	Body   string
}

func NewPost(e *imap.Email) (*Post, error) {

	// TODO: Check email fields for content, format
	// TODO: Sanitize email fields if needed

	// TODO: This could be more deterministic...
	var author string
	for address, name := range e.From {
		author = name
	}

	p := &Post{
		Title:  e.Subject,
		Author: author,
		Posted: e.Received,
		Body:   e.HTML,
	}

	// TODO: If email HTML field is empty, use the Text field

	// TODO: Test for errors and return them

	return p, nil
}

func main() {
	fmt.Println("preposterus starting up...")

	// TODO: Parse command line args
	// TODO: Load config if avaliable
	// TODO: Check for a new email
	// TODO: Parse email
	// TODO: Check for existing blog for sender
	// TODO: Initialize new blog directory
	// TODO: Write-out new blog post
	// TODO: Update blog index
	// TODO: Update RSS feeds
	// TODO: Mark email as read

	fmt.Println("preposterus done!")
}
