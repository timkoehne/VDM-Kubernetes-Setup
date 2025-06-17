package main

import (
	"bytes"
	"image"
	"net/http"

	"github.com/disintegration/imaging"
)

func processHandler(w http.ResponseWriter, r *http.Request) {
	file, _, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "File required", http.StatusBadRequest)
		return
	}
	defer file.Close()

	srcImg, _, err := image.Decode(file)
	if err != nil {
		http.Error(w, "Invalid image", http.StatusBadRequest)
		return
	}

	grayImg := imaging.Grayscale(srcImg)

	buf := new(bytes.Buffer)
	err = imaging.Encode(buf, grayImg, imaging.PNG)
	if err != nil {
		http.Error(w, "Failed to encode image", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "image/png")
	w.Write(buf.Bytes())
}

func healthzHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"ok"}`))
}

func main() {
	http.HandleFunc("/process", processHandler)
	http.HandleFunc("/healthz", healthzHandler)

	http.ListenAndServe(":8000", nil)
}
