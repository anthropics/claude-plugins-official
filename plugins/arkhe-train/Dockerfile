FROM ghcr.io/ggerganov/llama.cpp:server

# Copy the generated GGUF model into the container
COPY arkhe-os.gguf /models/arkhe-os.gguf

# Expose the default port
EXPOSE 8080

# Run the llama.cpp server with the model
ENTRYPOINT ["/server"]
CMD ["-m", "/models/arkhe-os.gguf", "--host", "0.0.0.0", "--port", "8080"]
