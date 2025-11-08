package main

import (
	"io/ioutil"
	"net/http"
	"strings"
	"testing"

	"github.com/stretchr/testify/require"
)

func TestPingEndpoint_Ping(t *testing.T) {
	resp, err := http.Get("http://localhost:5000/ping")
	if err != nil {
		t.Fatalf("Failed to GET /ping: %v", err)
	}
	defer resp.Body.Close()

	require.Equal(t, resp.StatusCode, http.StatusOK)

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		t.Fatalf("Failed to read body: %v", err)
	}

	require.Equal(t, "pong", strings.TrimSpace(string(body)))
}

func TestPingEndpoint_Visits(t *testing.T) {
	resp, err := http.Get("http://localhost:5000/visits")
	if err != nil {
		t.Fatalf("Failed to GET /visits: %v", err)
	}
	defer resp.Body.Close()

	require.Equal(t, resp.StatusCode, http.StatusOK)
}

func TestPingEndpoint_VisitsCache(t *testing.T) {
	resp, err := http.Get("http://localhost:5000/visits_cache")
	if err != nil {
		t.Fatalf("Failed to GET /visits_cache: %v", err)
	}
	defer resp.Body.Close()

	require.Equal(t, resp.StatusCode, http.StatusOK)
}
