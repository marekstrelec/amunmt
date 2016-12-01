#!/usr/bin/env python
import sys
import _pickle as cPickle
import json
import operator

d = cPickle.load(open(sys.argv[1], 'r'))
json.dump(d, sys.stdout)
