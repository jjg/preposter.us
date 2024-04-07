package main

import "testing"

func TestNewPost(t *testing.T) {
	want := "???"
	got := NewPost()

	if want != got {
		t.Fatalf("NewPost() = %v, wanted %s", got, want)
	}
}
