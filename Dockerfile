FROM gcr.io/distroless/python3
COPY --from=docker.io/rclone/rclone:1.67 /usr/local/bin/rclone /usr/local/bin/rclone
WORKDIR /app
COPY decayer.py /app/
ENV RCLONE_CONFIG=/dev/null
ENTRYPOINT ["python", "decayer.py"]
