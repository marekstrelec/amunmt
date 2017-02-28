// Copyright 2015 The Gemmlowp Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <unistd.h>
#ifdef __APPLE__
#include <sys/time.h>
#endif

#include <cstdint>
#include <cstdlib>
#include <ctime>
#include <iostream>
#include <map>
#include <vector>
#ifdef __APPLE__
#include <TargetConditionals.h>
#endif

#include "gemmlowp/test/test.h"
#include "mblas/matrix.h"
#include <random>
#include <boost/timer.hpp>

#ifndef GEMMLOWP_TEST_BIT_DEPTH_PARAMS
#define GEMMLOWP_TEST_BIT_DEPTH_PARAMS DefaultL8R8BitDepthParams
#endif

#if defined(__arm__) && !defined(GEMMLOWP_NEON)
#warning "Building without NEON support on ARM, check your compiler setup!"
#endif

#if defined(__SSE4_2__) && !defined(GEMMLOWP_SSE4)
#warning \
    "Building without SSE4.2 support on SSE4.2 enabled machine, check your compiler setup!"
#endif

using namespace std;
using namespace CPU;
using namespace boost;

namespace gemmlowp {

    random_device rd; // obtain a random number from hardware
    mt19937 eng(rd()); // seed the generator
    uniform_real_distribution<float> distr(-2.0, 2.0); // define the range

    mblas::Matrix createMatrix(int rows, int cols) {
      mblas::Matrix A;
      A.resize(rows, cols);

      for (int i=0; i<cols; i++) {
        for (int j=0; j<rows; j++) {
          A(j, i) = distr(eng);
        }
      }

      return A;
    }

double time() {
#ifdef __APPLE__
  timeval t;
  gettimeofday(&t, nullptr);
  return t.tv_sec + 1e-6 * t.tv_usec;
#else
  timespec t;
  clock_gettime(CLOCK_REALTIME, &t);
  return t.tv_sec + 1e-9 * t.tv_nsec;
#endif
}

const double min_accurate_duration = 1e-1;
const std::size_t min_working_set_size = 16 * 1024 * 1024;

struct gemm_t {
  int rows, depth, cols;
  gemm_t() : rows(0), depth(0), cols(0) {}
  gemm_t(int r, int d, int c) : rows(r), depth(d), cols(c) {}
};

bool operator<(const gemm_t& a, const gemm_t& b) {
  return a.rows < b.rows ||
         (a.rows <= b.rows &&
          (a.depth < b.depth || (a.depth <= b.depth && (a.cols < b.cols))));
}

double time_for_gemms() {
  typedef std::uint8_t Scalar;

  // set up the matrix pool

  int a = 12;
  int b = 500;
  int c = 85000;

  std::vector<mblas::Matrix> gemms_a;
  std::vector<mblas::Matrix> gemms_b;
  std::vector<mblas::Matrix> gemms_res;
  std::vector<double> times;

  for (int i=0; i<3; ++i) {
    gemms_a.push_back(createMatrix(a, b));
    gemms_b.push_back(createMatrix(b, c));
  }


  // main benchmark loop

  int iters_at_a_time = 1;
  float time_per_iter = 0.0f;

  while (true) {
    double starttime = time();
    for (int i = 0; i < iters_at_a_time; i++) {
      for (int j = 0; j < gemms_a.size(); j++) {
        timer tm1;
        gemms_res.push_back(gemms_a[j]*gemms_b[j]);
        times.push_back(tm1.elapsed());
      }
    }
    double endtime = time();

    const float timing = static_cast<float>(endtime - starttime);

    if (timing >= min_accurate_duration) {
      time_per_iter = timing / iters_at_a_time;
      break;
    }

    iters_at_a_time *= 2;
  }

  for (auto t: times){
    std::cout << t << std::endl;
  }
  std::cout << std::endl;

  return time_per_iter;
}

template <typename LhsType, typename RhsType, typename ResultType>
double gflops_for_gemms(GemmContext* context,
                        const std::vector<gemm_t>& gemms) {
  const double time_per_iter =
      time_for_gemms();
  double ops = 0;
  for (auto gemm : gemms) {
    ops += 2.0 * gemm.rows * gemm.depth * gemm.cols;
  }
  return 1e-9 * ops / time_per_iter;
}


void benchmark_gemm_sizes(GemmContext* context,
                          const std::vector<gemm_t>& gemms, double mintime) {
  typedef Matrix<std::uint8_t, MapOrder::RowMajor> LhsType;
  typedef Matrix<std::uint8_t, MapOrder::ColMajor> RhsType;
  typedef Matrix<std::uint8_t, MapOrder::ColMajor> ResultType;

  std::vector<float> gemm_times;
  std::cout << "running for " << mintime << " seconds..." << std::endl;

#ifdef GEMMLOWP_TEST_PROFILE
  gemmlowp::RegisterCurrentThreadForProfiling();
  gemmlowp::StartProfiling();
#endif

  double starttime = time();
  while (time() < starttime + mintime) {
    gemm_times.push_back(
        time_for_gemms());
  }

#ifdef GEMMLOWP_TEST_PROFILE
  gemmlowp::FinishProfiling();
#endif

  std::sort(gemm_times.begin(), gemm_times.end());

  double sum_gemm_times = 0;
  double sum_gemm_times_trimmed = 0;
  int count_gemm_times_trimmed = 0;
  const float trim_ratio = 0.25;
  const size_t count_trimmed = gemm_times.size() * trim_ratio;
  double sum_gemm_times_best = 0;
  int count_gemm_times_best = 0;
  const float best_ratio = 0.1;
  const size_t count_best = gemm_times.size() * best_ratio;

  for (size_t i = 0; i < gemm_times.size(); i++) {
    sum_gemm_times += gemm_times[i];
    if (i >= count_trimmed && i < gemm_times.size() - count_trimmed) {
      sum_gemm_times_trimmed += gemm_times[i];
      count_gemm_times_trimmed++;
    }
    if (i < count_best) {
      sum_gemm_times_best += gemm_times[i];
      count_gemm_times_best++;
    }
  }

  const double min_latency = gemm_times.front();
  const double max_latency = gemm_times.back();
  const double mean_latency = sum_gemm_times / gemm_times.size();
  const double trimmed_mean_latency =
      sum_gemm_times_trimmed / count_gemm_times_trimmed;
  const double best_mean_latency = sum_gemm_times_best / count_gemm_times_best;

  std::cout << "Graph latency (over " << gemm_times.size()
            << " iterations):" << std::endl;
  std::cout << "  Best:             " << min_latency << "s" << std::endl;
  std::cout << "  Worst:            " << max_latency << "s" << std::endl;
  std::cout << "  Mean:             " << mean_latency << "s" << std::endl;
  std::cout << "  " << 100 * trim_ratio
            << "% trimmed mean: " << trimmed_mean_latency << "s" << std::endl;
  std::cout << "  Mean of " << 100 * best_ratio
            << "% best: " << best_mean_latency << "s" << std::endl;
}


void benchmark_small_model(GemmContext* context) {
  // These are the m, n, k sizes for a small model with large batches.
  const int small_model_gemm_sizes[] = {
      29232, 16, 25, 7308, 6, 400, 203, 3002, 216,
  };
  assert(sizeof(small_model_gemm_sizes) %
             (3 * sizeof(small_model_gemm_sizes[0])) ==
         0);
  const std::size_t num_small_model_gemms =
      sizeof(small_model_gemm_sizes) / (3 * sizeof(small_model_gemm_sizes[0]));

  std::vector<gemm_t> small_model_gemms(num_small_model_gemms);
  for (std::size_t i = 0; i < num_small_model_gemms; i++) {
    small_model_gemms[i].rows = 12;
    small_model_gemms[i].depth = 500;
    small_model_gemms[i].cols = 85000;
  }

  const double mintime = 10.0;
  benchmark_gemm_sizes(context, small_model_gemms, mintime);
}

void benchmark_all() {
  {
    gemmlowp::GemmContext context;
    std::cout << "Benchmarking small model GEMMs..." << std::endl;
    gemmlowp::benchmark_small_model(&context);
  }

}

}  // end namespace gemmlowp

// For iOS, we need to define our own main(), so skip it here.
#if !(defined(__APPLE__) && (TARGET_OS_IPHONE || TARGET_IPHONE_SIMULATOR))
int main() { gemmlowp::benchmark_all(); }
#endif
