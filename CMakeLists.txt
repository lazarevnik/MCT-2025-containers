cmake_minimum_required(VERSION 3.10)
project(RestbedApp)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(/usr/local/include)
link_directories(/usr/local/lib)

find_library(RESTBED_LIB restbed)

add_executable(restbed-app src/main.cpp)

install(TARGETS restbed-app DESTINATION bin)

target_link_libraries(restbed-app ${RESTBED_LIB})
