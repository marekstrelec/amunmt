#!/bin/sh

c++ benchmark2.cc -I . --std=c++14 -msse4.1 -O3 -lpthread -o /tmp/quantization_example && /tmp/quantization_example
