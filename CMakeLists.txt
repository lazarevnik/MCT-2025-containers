cmake_minimum_required(VERSION 3.10)
project(RestbedApp)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(/usr/local/include)
link_directories(/usr/local/lib)

find_library(RESTBED_LIB restbed)

find_path(PQ_INCLUDE_DIR libpq-fe.h
    PATHS
    /usr/include
    /usr/include/postgresql
    /usr/local/include
    REQUIRED
)

find_library(PQ_LIBRARY
    NAMES pq
	PATHS
	/usr/lib
    /usr/lib/x86_64-linux-gnu
	/usr/local/lib
	REQUIRED
)

find_library(RESTBED_LIB NAMES restbed)
find_library(BOOST_SYSTEM_LIB NAMES boost_system)

include_directories(${PQ_INCLUDE_DIR})

if(DEFINED ENV{DEV})
    add_definitions(-DDEV)
endif()

add_executable(restbed-app src/main.cpp)

target_link_libraries(restbed-app 
    ${RESTBED_LIB}
    ${BOOST_SYSTEM_LIB}
    ${BOOST_COROUTINE_LIB}
    ${BOOST_CONTEXT_LIB}
    ${SSL_LIB}
    ${CRYPTO_LIB}
    ${PQ_LIBRARY}
    pthread
    dl
)

