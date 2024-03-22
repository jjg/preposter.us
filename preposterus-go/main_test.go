package main

import (
	"github.com/BrianLeishman/go-imap"
	"testing"
	"time"
)

func getTestEmail() *imap.Email {
	email := &imap.Email{
		From: imap.EmailAddresses{
			"nobody@email.com": "Mr. Nobody",
		},
		Subject:  "Hello, squirrel!",
		Received: time.Now(),
		Text:     "Fork the planet!",
		HTML:     "<h1>Fork the planet!</h1>",
		Attachments: []imap.Attachment{ // TODO: add one of each type of attachment we support
			imap.Attachment{
				Name:     "photo.jpg",
				MimeType: "image/jpeg",
				Content:  nil, // TODO: Add some real data here
			},
		},
	}

	return email
}

func TestParseCommandLine(t *testing.T) {
	t.Fatal("not implemented")
}

func TestLoadConfig(t *testing.T) {
	t.Fatal("not implemented")
}

func TestCheckForEmail(t *testing.T) {
	t.Fatal("not implemented")
}

func TestParseEmail(t *testing.T) {
	t.Fatal("not implemented")
}

func TestInitializeBlog(t *testing.T) {
	t.Fatal("not implemented")
}

func TestNewPost(t *testing.T) {

	p, err := NewPost(getTestEmail())

	if err != nil {
		t.Fatalf("Error creating blog entry: %v", err)
	}

	// TODO: Use table-driven test to test post properties
	if p.Title == "" {
		t.Fatalf("Post title missing!")
	}
	if p.Author == "" {
		t.Fatalf("Post author missing!")
	}
	if p.Posted.IsZero() {
		t.Fatalf("Post posted missing!")
	}
	if p.Body == "" {
		t.Fatalf("Post body missing!")
	}
}

func TestUpdateBlogIndex(t *testing.T) {
	t.Fatal("not implemented")
}

func TestUpdateRSSFeeds(t *testing.T) {
	t.Fatal("not implemented")
}

func TestMarkEmailAsRead(t *testing.T) {
	t.Fatal("not implemented")
}
