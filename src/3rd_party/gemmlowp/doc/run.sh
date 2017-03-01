#!/bin/sh

c++ quantization_example.cc -I . --std=c++14 -lpthread -fPIC -O3 -Ofast -m64 -flto -march=native -funroll-loops -ffinite-math-only -Wno-unused-result -Wno-deprecated -pthread -o /tmp/quantization_example && /tmp/quantization_example
