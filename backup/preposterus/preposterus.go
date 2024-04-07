package main

import "fmt"

type Post struct {
	title  string
	slug   string
	author string
	date   string
	url    string
	body   string
}

func (p *Post) NewPost() *Post {
	// TODO: initialize a new post instance and return it
	return &Post()
}

func (p *Post) Publish() {
	// TODO: write post to disk, update indexes and send notification to author
}

func main() {
	fmt.Println("This will be preposterus (eventually).")

	// TODO: parse command line args
	// TODO: fetch message
	// TODO: extract post components from email
	// TODO: find or create blog dir (copy stylesheet, create index, rss index, podcast?)
	// TODO: create file for post
	// TODO: update posts index, rss, podcast xml
	// TODO: update global posts index
	// TODO: send email notification to post author
}
