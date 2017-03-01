#ifndef AMUNN_QUANT_H
#define AMUNN_QUANT_H

#pragma once


#include <vector>
#include <sstream>
#include "../mblas/matrix.h"
#include "gemmlowp/test/test.h"
#include <3rd_party/gemmlowp/public/map.h>


namespace CPU {

    template<typename tScalar, gemmlowp::MapOrder tOrder>
    class MatrixWithStorage {
    public:

        MatrixWithStorage() {}

        MatrixWithStorage(int rows, int cols)
                : storage(rows * cols), matrix_map(storage.data(), rows, cols) {}

        void MakeRandom() {
            static std::mt19937 random_engine;
            std::uniform_real_distribution<float> distribution(-1, 1);
            for (auto &x : storage) {
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

        const std::vector<tScalar> &Storage() const { return storage; }

        std::vector<tScalar> &Storage() { return storage; }

    private:
        std::vector<tScalar> storage;
        gemmlowp::MatrixMap<tScalar, tOrder> matrix_map;
    };


    template<typename tScalar, gemmlowp::MapOrder tOrder>
    std::ostream &operator<<(std::ostream &s,
                             const MatrixWithStorage<tScalar, tOrder> &m) {
        return s << m.ConstMap();
    }


    typedef MatrixWithStorage<std::uint8_t, gemmlowp::MapOrder::ColMajor> StorageMatrix;
//    const auto kOrder = gemmlowp::MapOrder::ColMajor;


    struct QuantizationParams {
        float scale;
        std::uint8_t zero_point;
    };

    struct QuantizationData {
        StorageMatrix matrix;
        QuantizationParams params;
    };


    ////////////


    class Quant {
    public:
        virtual ~Quant();

        static std::string show(mblas::Matrix A, int row, int col);

        static mblas::Matrix createMatrix(int rows, int cols);


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

        static StorageMatrix
        compute_quantized_multiplication(QuantizationData uint8_ma_data1, QuantizationData uint8_ma_data2,
                                         QuantizationParams result_params);

    };

}

#endif //AMUNN_QUANT_H
