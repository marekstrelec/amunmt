#!/bin/sh

# c++ benchmark3.cc -I . --std=c++14 -msse4.1 -O3 -lpthread -o /tmp/quantization_example && /tmp/quantization_example
c++ benchmark3.cc -I . --std=c++14 -lpthread -fPIC -O3 -Ofast -m64 -flto -march=native -funroll-loops -ffinite-math-only -Wno-unused-result -Wno-deprecated -pthread -o /tmp/quantization_example && /tmp/quantization_example
