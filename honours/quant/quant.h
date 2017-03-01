#pragma once


#include <vector>
#include <sstream>
#include "../mblas/matrix.h"
#include "gemmlowp/test/test.h"
#include <3rd_party/gemmlowp/public/map.h>


using namespace CPU;


typedef gemmlowp::Matrix<std::uint8_t, gemmlowp::MapOrder::RowMajor> LhsType;
typedef gemmlowp::Matrix<std::uint8_t, gemmlowp::MapOrder::ColMajor> RhsType;
typedef gemmlowp::Matrix<std::uint8_t, gemmlowp::MapOrder::ColMajor> ResultType;


const auto kOrder = gemmlowp::MapOrder::ColMajor;

struct QuantizationParams {
    float scale;
    std::uint8_t zero_point;
};

struct QuantizationData {
    LhsType LhsMatrix;
    RhsType RhsMatrix;
    QuantizationParams params;
};


class quant {
public:
    virtual ~quant();

    static void show(mblas::Matrix A, int row, int col);

    static mblas::Matrix createMatrix(int rows, int cols);

////////////

    template<gemmlowp::MapOrder tOrder>
    static void FindMinMax(const gemmlowp::MatrixMap<float, tOrder> &m, float *min,
                           float *max);

    static void MyFindMinMax(mblas::Matrix A, float *min,
                             float *max);


    static QuantizationParams ChooseQuantizationParams(float min, float max);


    static void QuantizeMultiplierSmallerThanOne(float real_multiplier,
                                                 std::int32_t *quantized_multiplier,
                                                 int *right_shift);

    static void
    Quantize(const QuantizationParams &qparams, const std::vector<float> &src, std::vector<std::uint8_t> *dst);

    static void Dequantize(const QuantizationParams &qparams,
                           const std::vector<std::uint8_t> &src, mblas::Matrix *dst);


////////////////


    static const std::vector<float> get_storage(mblas::Matrix A);

    static QuantizationData get_quantized_matrix(mblas::Matrix A);

    static ResultType compute_quantized_multiplication(QuantizationData uint8_ma_data1, QuantizationData uint8_ma_data2,
                                                       QuantizationParams result_params);

};
