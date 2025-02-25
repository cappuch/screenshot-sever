package main

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"
)

type Config struct {
	AuthToken string `yaml:"auth_token"`
	Port      int    `yaml:"port"`
}

var (
	uploadDir string
	authKey   string
)

func generateRandomString(length int) string {
	bytes := make([]byte, length)
	rand.Read(bytes)
	return hex.EncodeToString(bytes)
}

func generateFilename(originalFilename string) string {
	randomName := generateRandomString(4)
	ext := filepath.Ext(originalFilename)
	if ext != "" {
		return randomName + ext
	}
	return randomName
}

// thank u claude for helping me fix this terrible code
func loadOrCreateConfig() (string, int) {
	configPath := "config.yml"
	var config Config

	configData, err := os.ReadFile(configPath)
	if err == nil {
		if err := yaml.Unmarshal(configData, &config); err == nil {
			if config.AuthToken != "" {
				fmt.Println("auth_token loaded from config file")
				if config.Port == 0 {
					config.Port = 80
				}
				return config.AuthToken, config.Port
			}
		}
	}

	newToken := generateRandomString(16)
	config.AuthToken = newToken
	config.Port = 80

	data, _ := yaml.Marshal(&config)
	if err := os.WriteFile(configPath, data, 0644); err != nil {
		log.Printf("Warning: couldn't write config file: %v", err)
	}

	if os.IsNotExist(err) {
		fmt.Printf("ALERT! No config file found. Generating a new one: %s\n", configPath)
	} else {
		fmt.Printf("ALERT! No auth_token found in %s. Generating a new one: %s\n", configPath, newToken)
	}

	return newToken, config.Port
}

func uploadHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	if r.Header.Get("Authorization") != authKey {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	file, header, err := r.FormFile("file")
	if err != nil {
		json.NewEncoder(w).Encode(map[string]string{"error": "No file part"})
		return
	}
	defer file.Close()

	if header.Filename == "" {
		json.NewEncoder(w).Encode(map[string]string{"error": "No selected file"})
		return
	}

	newFilename := generateFilename(header.Filename)
	filepath := filepath.Join(uploadDir, newFilename)

	dst, err := os.Create(filepath)
	if err != nil {
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}
	defer dst.Close()

	if _, err := io.Copy(dst, file); err != nil {
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	scheme := "http"
	if r.TLS != nil {
		scheme = "https"
	}
	fileURL := fmt.Sprintf("%s://%s/files/%s", scheme, r.Host, newFilename)
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"url": fileURL})
}

func fileHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	filename := strings.TrimPrefix(r.URL.Path, "/files/")
	http.ServeFile(w, r, filepath.Join(uploadDir, filename))
}

func robotsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain")
	w.Write([]byte("User-agent: *\nDisallow: /"))
}

func main() {
	var err error
	uploadDir, err = filepath.Abs("uploads")
	if err != nil {
		log.Fatal(err)
	}

	if err := os.MkdirAll(uploadDir, 0755); err != nil {
		log.Fatal(err)
	}

	var port int
	authKey, port = loadOrCreateConfig()

	http.HandleFunc("/upload", uploadHandler)
	http.HandleFunc("/files/", fileHandler)
	http.HandleFunc("/robots.txt", robotsHandler)

	addr := fmt.Sprintf(":%d", port)
	fmt.Printf("Server starting on %s\n", addr)
	log.Fatal(http.ListenAndServe(addr, nil))
}