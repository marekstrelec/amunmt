
#include <iostream>
#include <vector>
#include <sstream>
#include "mblas/matrix.h"
#include <boost/timer.hpp>


#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>
#include "gemmlowp/public/gemmlowp.h"
#include "gemmlowp/public/output_stages.h"

#include <ctime>


using namespace std;
using namespace CPU;
using namespace boost;


random_device rd; // obtain a random number from hardware
mt19937 eng(rd()); // seed the generator
uniform_real_distribution<float> distr(-2.0, 2.0); // define the range


const auto kOrder = gemmlowp::MapOrder::ColMajor;


void show(mblas::Matrix A, int row, int col) {
    for (int i=0; i<row; i++) {
        for (int j=0; j<col; j++) {
            cout << A(i, j) << " ";
        }
        cout << endl;
    }
}

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





////////////

struct QuantizationParams {
    float scale;
    std::uint8_t zero_point;
};

// Output a matrix to a std::ostream
template <typename tScalar, gemmlowp::MapOrder tOrder>
std::ostream& operator<<(std::ostream& s,
                         const gemmlowp::MatrixMap<tScalar, tOrder>& m) {
    for (int i = 0; i < m.rows(); i++) {
        for (int j = 0; j < m.cols(); j++) {
            if (j) {
                s << '\t';
            }
            s << static_cast<float>(m(i, j));
        }
        s << '\n';
    }
    return s;
}


template <typename tScalar, gemmlowp::MapOrder tOrder>
class MatrixWithStorage {
public:
    MatrixWithStorage(int rows, int cols)
            : storage(rows * cols), matrix_map(storage.data(), rows, cols) {}

    MatrixWithStorage() {}

    void MakeRandom() {
        static std::mt19937 random_engine;
        std::uniform_real_distribution<float> distribution(-1, 1);
        for (auto& x : storage) {
            x = static_cast<tScalar>(distribution(random_engine));
        }
    }
    gemmlowp::MatrixMap<const tScalar, tOrder> ConstMap() const {
        return gemmlowp::MatrixMap<const tScalar, tOrder>(
                storage.data(), matrix_map.rows(), matrix_map.cols());
    }
    gemmlowp::MatrixMap<tScalar, tOrder> Map() {
        return gemmlowp::MatrixMap<tScalar, tOrder>(
                storage.data(), matrix_map.rows(), matrix_map.cols());
    }
    const std::vector<tScalar>& Storage() const { return storage; }
    std::vector<tScalar>& Storage() { return storage; }

private:
    std::vector<tScalar> storage;
    gemmlowp::MatrixMap<tScalar, tOrder> matrix_map;
};

template <typename tScalar, gemmlowp::MapOrder tOrder>
std::ostream& operator<<(std::ostream& s,
                         const MatrixWithStorage<tScalar, tOrder>& m) {
    return s << m.ConstMap();
}


template <gemmlowp::MapOrder tOrder>
void FindMinMax(const gemmlowp::MatrixMap<float, tOrder>& m, float* min,
                float* max) {
    *min = *max = m(0, 0);
    for (int i = 0; i < m.rows(); i++) {
        for (int j = 0; j < m.cols(); j++) {
            const float val = m(i, j);
            *min = std::min(*min, val);
            *max = std::max(*max, val);
        }
    }
}

void MyFindMinMax(mblas::Matrix A, float* min,
                float* max) {
    *min = *max = A(0, 0);
    for (int i = 0; i < A.rows(); i++) {
        for (int j = 0; j < A.columns(); j++) {
            const float val = A(i, j);
            *min = std::min(*min, val);
            *max = std::max(*max, val);
        }
    }
}


QuantizationParams ChooseQuantizationParams(float min, float max) {
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


void QuantizeMultiplierSmallerThanOne(float real_multiplier,
                                      std::int32_t* quantized_multiplier,
                                      int* right_shift) {
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

void Quantize(const QuantizationParams& qparams, const std::vector<float>& src, std::vector<std::uint8_t>* dst) {
    assert(src.size() == dst->size());
    for (std::size_t i = 0; i < src.size(); i++) {
        const float real_val = src[i];
        const float transformed_val = qparams.zero_point + real_val / qparams.scale;
        const float clamped_val = std::max(0.f, std::min(255.f, transformed_val));
        (*dst)[i] = static_cast<std::uint8_t>(std::round(clamped_val));
    }
}

void Dequantize(const QuantizationParams& qparams,
                const std::vector<std::uint8_t>& src, mblas::Matrix* dst) {
    int rows = (*dst).rows();
    assert(src.size() == rows*(*dst).columns());
    for (std::size_t i = 0; i < src.size(); i++) {
        const std::uint8_t quantized_val = src[i];
        int r = i % rows;
        int c = i / rows;
        (*dst)(r, c) = qparams.scale * (quantized_val - qparams.zero_point);
    }
}


////////////////


const std::vector<float> get_storage(mblas::Matrix A){
    std::vector<float> vecf;
    for (int i = 0; i < A.columns(); i++) {
        for (int j = 0; j < A.rows(); j++) {
            vecf.push_back((float &&) (A(j, i)));
        }
    }

    return vecf;
}

struct QuantizationData {
    MatrixWithStorage<std::uint8_t, kOrder> matrix;
    QuantizationParams params;

};

QuantizationData get_quantized_matrix(mblas::Matrix A) {
    QuantizationData dest;

    float a_min, a_max;
    MyFindMinMax(A, &a_min, &a_max);
    QuantizationParams a_qparams = ChooseQuantizationParams(a_min, a_max);

    const std::vector<float>& src_mm = get_storage(A);
    MatrixWithStorage<std::uint8_t, kOrder> uint8_mm(A.rows(), A.columns());
    Quantize(a_qparams, src_mm, &uint8_mm.Storage());

    dest.params = a_qparams;
    dest.matrix = uint8_mm;

    return dest;

}

MatrixWithStorage<std::uint8_t, kOrder> compute_quantized_multiplication(QuantizationData uint8_ma_data1, QuantizationData uint8_ma_data2, QuantizationParams result_params) {

    MatrixWithStorage<std::uint8_t, kOrder> uint8_ma_result(uint8_ma_data1.matrix.Map().rows(), uint8_ma_data2.matrix.Map().cols());

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
    const auto& output_pipeline =
            std::make_tuple(quantize_down_stage, saturating_cast_stage);

    auto actual_uint8_result_map = uint8_ma_result.Map();
    gemmlowp::GemmContext gemm_context;
    gemmlowp::GemmWithOutputPipeline<std::uint8_t, std::uint8_t,
            gemmlowp::DefaultL8R8BitDepthParams>(
            &gemm_context, uint8_ma_data1.matrix.ConstMap(), uint8_ma_data2.matrix.ConstMap(),
            &actual_uint8_result_map, lhs_offset, rhs_offset, output_pipeline);

    return uint8_ma_result;
}


void test() {
    int a = 5;
    int b = 10;
    int c = 7;

    // define matrices
    cout << "1";
    mblas::Matrix ma = createMatrix(a, b);
    mblas::Matrix mb = createMatrix(b, c);
    mblas::Matrix m_result = ma * mb;

    cout << "2";

    QuantizationData uint8_ma_data1 = get_quantized_matrix(ma);
    QuantizationData uint8_ma_data2 = get_quantized_matrix(mb);

    cout << "3";

    // find result params
    float res_min, res_max;
    MyFindMinMax(m_result, &res_min, &res_max);
    QuantizationParams result_params = ChooseQuantizationParams(res_min, res_max);
//    QuantizationParams result_params;
//    result_params.scale = 0.02;
//    result_params.zero_point = (std::uint8_t) 150;

    cout << "Matrix A: " << endl;
    show(ma, a, b);
    cout << endl;

    cout << "Matrix B: " << endl;
    show(mb, b, c);
    cout << endl;

    cout << "My Quantized uint8 matrix A:\n" << uint8_ma_data1.matrix << endl;
    cout << "My Quantized uint8 matrix B:\n" << uint8_ma_data2.matrix << endl;

    MatrixWithStorage<std::uint8_t, kOrder> uint8_ma_result = compute_quantized_multiplication(uint8_ma_data1, uint8_ma_data2, result_params);
    cout << "Quantized uint8 result matrix obtained by quantized multiplication:\n"
         << uint8_ma_result << endl;


    cout << "\n\n\nNormal result AxB: " << endl;
    show(m_result, a, c);
    cout << endl;


    mblas::Matrix m_res(uint8_ma_data1.matrix.Map().rows(), uint8_ma_data2.matrix.Map().cols());
    Dequantize(result_params, uint8_ma_result.Storage(),
               &m_res);

    cout    << "\nQuantized result AxB: " << endl;
    show(m_res, m_res.rows(), m_res.columns());


    float error = 0;
    for (int i = 0; i < m_res.rows(); i++) {
        for (int j = 0; j < m_res.columns(); j++) {
            error += std::abs(m_res(i, j) - m_result(i, j));
        }
    }

    cout << "ERROR: " << error << endl;
}

void test2(){
    int a = 12;
    int b = 500;
    int c = 85000;

    // define matrices
    mblas::Matrix ma = createMatrix(a, b);
    mblas::Matrix mb = createMatrix(b, c);
    mblas::Matrix m_res(a, c);

    timer ti0;
    QuantizationData uint8_ma_data1 = get_quantized_matrix(ma);
    double elapsed_time0 = ti0.elapsed();

    QuantizationData uint8_ma_data2 = get_quantized_matrix(mb);


    QuantizationParams result_params;
    result_params.scale = 0.02;
    result_params.zero_point = (std::uint8_t) 150;

    timer ti1;
    MatrixWithStorage<std::uint8_t, kOrder> uint8_ma_result = compute_quantized_multiplication(uint8_ma_data1, uint8_ma_data2, result_params);
    double elapsed_time1 = ti1.elapsed();
    timer ti2;
    Dequantize(result_params, uint8_ma_result.Storage(), &m_res);

    double elapsed_time2 = ti2.elapsed();
    cout << "Time: " << elapsed_time0 << " x " << elapsed_time1 << " x " << elapsed_time2 << endl;
    cout << "Total time: " << elapsed_time0 + elapsed_time1 + elapsed_time2;
}

void test3() {
    cout << "START" << endl;

    QuantizationParams result_params;
//    result_params.scale = 0.02;
//    result_params.zero_point = (std::uint8_t) 150;
    result_params.scale = 1.1;
    result_params.zero_point = (std::uint8_t) 130;

    int epochs = 1;
    float normal_total_time = 0;
    float quant_total_time = 0;
    for (int e=0; e<epochs; ++e) {
        int N = 1;
        int R1 = 12;
        int C1 = 500;
        int C2 = 85000;

        vector <mblas::Matrix> matrices1;
        vector <mblas::Matrix> matrices2;
        vector <mblas::Matrix> matrices3;
        vector <QuantizationData> q_data1;
        vector <QuantizationData> q_data2;
        vector <mblas::Matrix> q_data3;


        // create random matrices
        for (int i = 0; i < N; ++i) {
            matrices1.push_back(createMatrix(R1, C1));
            matrices2.push_back(createMatrix(C1, C2));

            q_data1.push_back(get_quantized_matrix(matrices1.back()));
            q_data2.push_back(get_quantized_matrix(matrices2.back()));
        }

        // compute normal
        timer ti;
        for (int i = 0; i < N; ++i) {
            matrices3.push_back(matrices1[i] * matrices2[i]);

//            float res_min, res_max;
//            MyFindMinMax(matrices3.back(), &res_min, &res_max);
//            QuantizationParams result_params = ChooseQuantizationParams(res_min, res_max);
//            cout << result_params.scale << endl;
//            cout << (float) result_params.zero_point << endl;
        }
        double elapsed_time = ti.elapsed();
        normal_total_time += elapsed_time;

        // compute quant
        for (int i = 0; i < N; ++i) {
            mblas::Matrix m_res(R1, C2);
            q_data3.push_back(m_res);
        }
        timer ti2;
        for (int i = 0; i < N; ++i) {
            MatrixWithStorage<std::uint8_t, kOrder> uint8_result = compute_quantized_multiplication(q_data1[i], q_data2[i], result_params);
            Dequantize(result_params, uint8_result.Storage(), &q_data3[i]);
        }
        double elapsed_time2 = ti2.elapsed();
        quant_total_time += elapsed_time2;

        cout << "epoch #" << e << " time: " << elapsed_time << " x " << elapsed_time2 << endl;

//        show(matrices3[0], 3, 5);
//        show(q_data3[0], 3, 5);
    }

    cout << "Final normal time: " << normal_total_time << endl;
    cout << "Final quant time: " << quant_total_time << endl;
    cout << "END" << endl;
}

void test4() {
    int a = 12;
    int b = 500;
    int c = 85000;
    mblas::Matrix A = createMatrix(a, b);
    mblas::Matrix B = createMatrix(b, c);
    mblas::MatrixSmall As = createMatrix(a, b);
    mblas::MatrixSmall Bs = createMatrix(b, c);

    timer ti1;
    mblas::Matrix C = A*B;
    double elapsed_time1 = ti1.elapsed();

    timer ti2;
    mblas::MatrixSmall Cs = A*B;
    double elapsed_time2 = ti2.elapsed();

    cout << "time: " << elapsed_time1 << " x " << elapsed_time2 << endl;

    show(C, 3, 3);
    show(Cs, 3, 3);
}

void test4_2() {
    /*
     * Experimenting with mblas matrices
     * rowMajor X rowMajor, and, rowMajor X columnMajor
     */
    int a = 12;
    int b = 500;
    int c = 85000;
    mblas::Matrix A = createMatrix(a, b);
    mblas::Matrix B = createMatrix(b, c);
    mblas::Matrix Ac = createMatrix(a, b);
    mblas::MatrixCol Bc = createMatrix(b, c);

    timer ti1;
    mblas::Matrix C = A*B;
    double elapsed_time1 = ti1.elapsed();

    timer ti2;
    mblas::Matrix Cc = Ac*Bc;
    double elapsed_time2 = ti2.elapsed();

    cout << "time: " << elapsed_time1 << " x " << elapsed_time2 << endl;

}


void test5() {
    int a = 12;
    int b = 500;
    int c = 85000;
    mblas::Matrix A = createMatrix(a, b);
    mblas::Matrix B = createMatrix(b, c);


    timer tm1;
    mblas::Matrix C = A*B;
    double elapsed_time1 = tm1.elapsed();

    timer tm2;
    mblas::Softmax(C);
    double elapsed_time2 = tm2.elapsed();

    cout << "time: " << elapsed_time1 << " x " << elapsed_time2 << endl;


    timer ti1;
}

int main(){

    test5();






    return 0;
}

