FROM messense/rust-musl-cross:x86_64-musl as builder

# Disable static query checks
ENV SQLX_OFFLINE=true
WORKDIR /ping-visits
COPY . .
RUN cargo b -r --target x86_64-unknown-linux-musl

# Create a new stage with minimal image
FROM scratch
COPY --from=builder /ping-visits/target/x86_64-unknown-linux-musl/release/ping-visits /ping-visits
EXPOSE 8080
ENTRYPOINT ["/ping-visits"]
