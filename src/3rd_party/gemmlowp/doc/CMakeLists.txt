cmake_minimum_required(VERSION 3.6)
project(doc_quant)

#set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_FLAGS_RELEASE "-std=c++14 -msse4.1 -fPIC -O3 -Ofast -m64 -flto -march=native -funroll-loops -ffinite-math-only -Wno-unused-result -Wno-deprecated -pthread")
set(CMAKE_CXX_FLAGS_DEBUG "-std=c++14 -msse4.1 -fPIC -g -m64 -flto -march=native -funroll-loops -ffinite-math-only -Wno-unused-result -Wno-deprecated -pthread")
set(CMAKE_CXX_FLAGS_PROFILE "${CMAKE_CXX_FLAGS_RELEASE} -g -pg")
set(CMAKE_CXX_FLAGS ${CMAKE_CXX_FLAGS_RELEASE})

include_directories(${CMAKE_CURRENT_SOURCE_DIR})

find_package(Boost COMPONENTS system filesystem program_options timer iostreams python thread)
if(Boost_FOUND)
    include_directories(${Boost_INCLUDE_DIRS})
    set(EXT_LIBS ${EXT_LIBS} ${Boost_LIBRARIES})
else(Boost_FOUND)
    message(SEND_ERROR "Cannot find Boost libraries. Terminating." )
endif(Boost_FOUND)

set(SOURCE_FILES quantization_example.cc)
add_executable(doc_quant ${SOURCE_FILES})