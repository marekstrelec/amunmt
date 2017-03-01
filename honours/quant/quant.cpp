#pragma once

#include "quant.h"

#include <iostream>
#include <vector>
#include <sstream>
#include "../mblas/matrix.h"
#include <boost/timer.hpp>


#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>
#include "../../3rd_party/gemmlowp/public/gemmlowp.h"
#include "../../3rd_party/gemmlowp/public/output_stages.h"

#include <ctime>


using namespace std;
using namespace CPU;
using namespace boost;


random_device rd; // obtain a random number from hardware
mt19937 eng(rd()); // seed the generator
uniform_real_distribution<float> distr(-2.0, 2.0); // define the range









void quant::show(mblas::Matrix A, int row, int col) {
    for (int i = 0; i < row; i++) {
        for (int j = 0; j < col; j++) {
            cout << A(i, j) << " ";
        }
        cout << endl;
    }
}

mblas::Matrix quant::createMatrix(int rows, int cols) {
    mblas::Matrix A;
    A.resize(rows, cols);

    for (int i = 0; i < cols; i++) {
        for (int j = 0; j < rows; j++) {
            A(j, i) = distr(eng);
        }
    }

    return A;
}


void quant::MyFindMinMax(mblas::Matrix A, float *min, float *max) {
    *min = *max = A(0, 0);
    for (int i = 0; i < A.rows(); i++) {
        for (int j = 0; j < A.columns(); j++) {
            const float val = A(i, j);
            *min = std::min(*min, val);
            *max = std::max(*max, val);
        }
    }
}

QuantizationParams quant::ChooseQuantizationParams(float min, float max) {
    min = std::min(min, 0.f);
    max = std::max(max, 0.f);

    // the min and max quantized values, as floating-point values
    const float qmin = 0;
    const float qmax = 255;

    // First determine the scale.
    const double scale = (max - min) / (qmax - qmin);

    const double initial_zero_point = qmin - min / scale;

    std::uint8_t nudged_zero_point = 0;
    if (initial_zero_point < qmin) {
        nudged_zero_point = qmin;
    } else if (initial_zero_point > qmax) {
        nudged_zero_point = qmax;
    } else {
        nudged_zero_point =
                static_cast<std::uint8_t>(std::round(initial_zero_point));
    }

    QuantizationParams result;
    result.scale = scale;
    result.zero_point = nudged_zero_point;
    return result;
}

void
quant::QuantizeMultiplierSmallerThanOne(float real_multiplier, std::int32_t *quantized_multiplier, int *right_shift) {
    assert(real_multiplier > 0.f);
    assert(real_multiplier < 1.f);
    int s = 0;
    // We want to bring the real multiplier into the interval [1/2, 1).
    // We can do so by multiplying it by two, and recording how many times
    // we multiplied by two so that we can compensate that by a right
    // shift by the same amount.
    while (real_multiplier < 0.5f) {
        real_multiplier *= 2.0f;
        s++;
    }
    // Now that the real multiplier is in [1/2, 1), we convert it
    // into a fixed-point number.
    std::int64_t q =
            static_cast<std::int64_t>(std::round(real_multiplier * (1ll << 31)));
    assert(q <= (1ll << 31));
    // Handle the special case when the real multiplier was so close to 1
    // that its fixed-point approximation was undistinguishable from 1.
    // We handle this by dividing it by two, and remembering to decrement
    // the right shift amount.
    if (q == (1ll << 31)) {
        q /= 2;
        s--;
    }
    assert(s >= 0);
    assert(q <= std::numeric_limits<std::int32_t>::max());
    *quantized_multiplier = static_cast<std::int32_t>(q);
    *right_shift = s;
}

void quant::Quantize(const QuantizationParams &qparams, const std::vector<float> &src, std::vector<uint8_t> *dst) {
    assert(src.size() == dst->size());
    for (std::size_t i = 0; i < src.size(); i++) {
        const float real_val = src[i];
        const float transformed_val = qparams.zero_point + real_val / qparams.scale;
        const float clamped_val = std::max(0.f, std::min(255.f, transformed_val));
        (*dst)[i] = static_cast<std::uint8_t>(std::round(clamped_val));
    }
}

void quant::Dequantize(const QuantizationParams &qparams, const std::vector<uint8_t> &src, mblas::Matrix *dst) {
    int rows = (*dst).rows();
    assert(src.size() == rows * (*dst).columns());
    for (std::size_t i = 0; i < src.size(); i++) {
        const std::uint8_t quantized_val = src[i];
        int r = i % rows;
        int c = i / rows;
        (*dst)(r, c) = qparams.scale * (quantized_val - qparams.zero_point);
    }
}

const std::vector<float> quant::get_storage(mblas::Matrix A) {
    std::vector<float> vecf;
    for (int i = 0; i < A.columns(); i++) {
        for (int j = 0; j < A.rows(); j++) {
            vecf.push_back((float &&) (A(j, i)));
        }
    }

    return vecf;
}

QuantizationData quant::get_quantized_matrix(mblas::Matrix A) {
    QuantizationData dest;

    float a_min, a_max;
    MyFindMinMax(A, &a_min, &a_max);
    QuantizationParams a_qparams;
    a_qparams = ChooseQuantizationParams(a_min, a_max);

    const std::vector<float> &src_mm = get_storage(A);
    MatrixWithStorage<std::uint8_t, kOrder> uint8_mm(A.rows(), A.columns());
    Quantize(a_qparams, src_mm, &uint8_mm.Storage());

    dest.params = a_qparams;
    dest.matrix = uint8_mm;

    return dest;

}

MatrixWithStorage <std::uint8_t, kOrder>
quant::compute_quantized_multiplication(QuantizationData uint8_ma_data1, QuantizationData uint8_ma_data2,
                                        QuantizationParams result_params) {

    MatrixWithStorage<std::uint8_t, kOrder> uint8_ma_result(uint8_ma_data1.matrix.Map().rows(),
                                                            uint8_ma_data2.matrix.Map().cols());

    const int lhs_offset = -uint8_ma_data1.params.zero_point;
    const int rhs_offset = -uint8_ma_data2.params.zero_point;
    const int result_offset = result_params.zero_point;

    const float real_multiplier =
            uint8_ma_data1.params.scale * uint8_ma_data2.params.scale / result_params.scale;
    std::int32_t quantized_multiplier;
    int right_shift;
    QuantizeMultiplierSmallerThanOne(real_multiplier, &quantized_multiplier,
                                     &right_shift);

    gemmlowp::OutputStageQuantizeDownInt32ToUint8ScaleByFixedPoint
            quantize_down_stage;
    quantize_down_stage.result_offset_after_shift = result_offset;
    quantize_down_stage.result_fixedpoint_multiplier = quantized_multiplier;
    quantize_down_stage.result_shift = right_shift;
    gemmlowp::OutputStageSaturatingCastToUint8 saturating_cast_stage;
    const auto &output_pipeline =
            std::make_tuple(quantize_down_stage, saturating_cast_stage);

    auto actual_uint8_result_map = uint8_ma_result.Map();
    gemmlowp::GemmContext gemm_context;
    gemmlowp::GemmWithOutputPipeline<std::uint8_t, std::uint8_t,
            gemmlowp::DefaultL8R8BitDepthParams>(
            &gemm_context, uint8_ma_data1.matrix.ConstMap(), uint8_ma_data2.matrix.ConstMap(),
            &actual_uint8_result_map, lhs_offset, rhs_offset, output_pipeline);

    return uint8_ma_result;
}

