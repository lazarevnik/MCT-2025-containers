FROM ubuntu:22.04 as builder

ARG DEV
ENV DEV $DEV

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    cmake \
    git \
    libboost-system-dev \
    libboost-coroutine-dev \
    libboost-context-dev \
    libasio-dev \
    libpq-dev

WORKDIR /tmp
RUN git clone https://github.com/corvusoft/restbed.git \
	 --branch 4.8 --single-branch && \
    cd restbed && \
    mkdir build && cd build && \
    cmake -DUSE_BOOST_ASIO=ON -DBUILD_SSL=OFF -DBUILD_TESTS=OFF \
          -DCMAKE_CXX_FLAGS="-Wno-narrowing" .. && \
    make && make install

# Copy restbed libraries and includes
RUN cd restbed/distribution && \
    cp -r include/* /usr/local/include/ && \
    cp library/librestbed.* /usr/local/lib/

# Copy app sources
WORKDIR /app
COPY . .

# Build application
RUN mkdir build && cd build && \
    cmake .. && \
    make


# Create minimal image
FROM ubuntu:22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy applictaion build from builder stage
COPY --from=builder /usr/local/lib/librestbed.* /usr/local/lib/
COPY --from=builder /app/build/restbed-app /usr/local/bin/

# Update libraries
RUN ldconfig

# Create user 
RUN useradd -m appuser
USER appuser
WORKDIR /home/appuser

# Run application
CMD ["/usr/local/bin/restbed-app"]
