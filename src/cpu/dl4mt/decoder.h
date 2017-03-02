#pragma once

#include <queue>
#include <vector>
#include <algorithm>

#include "../mblas/matrix.h"
#include "model.h"
#include "gru.h"
#include "common/god.h"

#include "common/vocab.h"
#include <math.h>

#include <boost/timer.hpp>
#include "quant.h"


namespace CPU {

class Decoder {
  private:
    template <class Weights>
    class Embeddings {
      public:
        Embeddings(const Weights& model)
        : w_(model)
        {}

        void Lookup(mblas::Matrix& Rows, const std::vector<size_t>& ids) {
          using namespace mblas;
          std::vector<size_t> tids = ids;
          for(auto&& id : tids)
            if(id >= w_.E_.rows())
              id = 1;
          Rows = Assemble<byRow, Matrix>(w_.E_, tids);
        }

        size_t GetCols() {
          return w_.E_.columns();
        }

        size_t GetRows() const {
          return w_.E_.rows();
        }

      private:
        const Weights& w_;
    };

    //////////////////////////////////////////////////////////////
    template <class Weights1, class Weights2>
    class RNNHidden {
      public:
        RNNHidden(const Weights1& initModel, const Weights2& gruModel)
        : w_(initModel), gru_(gruModel) {}

        void InitializeState(mblas::Matrix& State,
                             const mblas::Matrix& SourceContext,
                             const size_t batchSize = 1) {
          using namespace mblas;

          // Calculate mean of source context, rowwise
          // Repeat mean batchSize times by broadcasting
          Temp1_ = Mean<byRow, Matrix>(SourceContext);
          Temp2_.resize(batchSize, SourceContext.columns());
          Temp2_ = 0.0f;
          AddBiasVector<byRow>(Temp2_, Temp1_);

          State = Temp2_ * w_.Wi_;
          AddBiasVector<byRow>(State, w_.Bi_);

          State = blaze::forEach(State, Tanh());
        }

        void GetNextState(mblas::Matrix& NextState,
                          const mblas::Matrix& State,
                          const mblas::Matrix& Context) {
          gru_.GetNextState(NextState, State, Context);
        }

      private:
        const Weights1& w_;
        const GRU<Weights2> gru_;

        mblas::Matrix Temp1_;
        mblas::Matrix Temp2_;
    };

    //////////////////////////////////////////////////////////////
    template <class Weights>
    class RNNFinal {
      public:
        RNNFinal(const Weights& model)
        : gru_(model) {}

        void GetNextState(mblas::Matrix& NextState,
                          const mblas::Matrix& State,
                          const mblas::Matrix& Context) {
          gru_.GetNextState(NextState, State, Context);
        }

      private:
        const GRU<Weights> gru_;
    };

    //////////////////////////////////////////////////////////////
    template <class Weights>
    class Attention {
      public:
        Attention(const Weights& model)
        : w_(model)
        {
          V_ = blaze::trans(blaze::row(w_.V_, 0));
        }

        void Init(const mblas::Matrix& SourceContext) {
          using namespace mblas;
          SCU_ = SourceContext * w_.U_;
          AddBiasVector<byRow>(SCU_, w_.B_);
        }

        void GetAlignedSourceContext(mblas::Matrix& AlignedSourceContext,
                                     const mblas::Matrix& HiddenState,
                                     const mblas::Matrix& SourceContext) {
          using namespace mblas;

          Temp2_ = HiddenState * w_.W_;

          // For batching: create an A across different sentences,
          // maybe by mapping and looping. In the and join different
          // alignment matrices into one
          // Or masking?
          Temp1_ = Broadcast<Matrix>(Tanh(), SCU_, Temp2_);

          A_.resize(Temp1_.rows(), 1);
          blaze::column(A_, 0) = Temp1_ * V_;
          size_t words = SourceContext.rows();
          // batch size, for batching, divide by numer of sentences
          size_t batchSize = HiddenState.rows();
          Reshape(A_, batchSize, words); // due to broadcasting above

          float bias = w_.C_(0,0);
          blaze::forEach(A_, [=](float x) { return x + bias; });

          mblas::Softmax(A_);
          AlignedSourceContext = A_ * SourceContext;
        }

        void GetAttention(mblas::Matrix& Attention) {
          Attention = A_;
        }

        mblas::Matrix& GetAttention() {
          return A_;
        }

      private:
        const Weights& w_;

        mblas::Matrix SCU_;
        mblas::Matrix Temp1_;
        mblas::Matrix Temp2_;
        mblas::Matrix A_;
        mblas::ColumnVector V_;
    };

    //////////////////////////////////////////////////////////////
    template <class Weights>
    class Softmax {
      public:
        Softmax(const Weights& model)
        : w_(model),
        filtered_(false)
        {}



        void GetProbs(mblas::ArrayMatrix& Probs,
                  const mblas::Matrix& State,
                  const mblas::Matrix& Embedding,
                  const mblas::Matrix& AlignedSourceContext) {
          using namespace mblas;

          T1_ = State * w_.W1_;
          T2_ = Embedding * w_.W2_;
          T3_ = AlignedSourceContext * w_.W3_;

          AddBiasVector<byRow>(T1_, w_.B1_);
          AddBiasVector<byRow>(T2_, w_.B2_);
          AddBiasVector<byRow>(T3_, w_.B3_);

          auto t = blaze::forEach(T1_ + T2_ + T3_, Tanh());

          if (true) {
              std::stringstream ss;
              // QUANTIZATION
              boost::timer tm1;
              mblas::Matrix dequant_result(t.rows(), w_.W4_.columns());
              QuantizationData qd_t = Quant::get_quantized_matrix(t);
              ss << tm1.elapsed() << " x ";

//              boost::timer tm2;
//              float res_min, res_max;
//              Quant::MyFindMinMax(t * w_.W4_, &res_min, &res_max);
//              QuantizationParams result_params = Quant::ChooseQuantizationParams(res_min, res_max);
//              ss << tm2.elapsed() << " x ";

//              float res_min = -20.f;
//              float res_max = 25.f;
//              QuantizationParams result_params = Quant::ChooseQuantizationParams(res_min, res_max);
              QuantizationParams result_params;
              result_params.scale = 0.176471;
              result_params.zero_point = 113;


              boost::timer tm3;
              StorageMatrix uint8_result = Quant::compute_quantized_multiplication(qd_t, w_.W4_quant, result_params);
              Quant::Dequantize(result_params, uint8_result.Storage(), &dequant_result);
              ss << tm3.elapsed() << " x ";

              Probs_ = dequant_result;
              AddBiasVector<byRow>(Probs_, w_.B4_);
//              God::WriteLog("quant_info", ss.str());

          } else if (!filtered_) {
            Probs_ = t * w_.W4_;
            AddBiasVector<byRow>(Probs_, w_.B4_);
          } else {
            Probs_ = t * FilteredW4_;
            AddBiasVector<byRow>(Probs_, FilteredB4_);
          }




            // find min and max values of Probs_
//            float p_min = 9999;
//            float p_max = -9999;
//
//            for (int i = 0; i < Probs_.rows(); i++) {
//                for (int j = 0; j < Probs_.columns(); j++) {
//                    const float val = Probs_(i, j);
//                    p_min = (std::min)(p_min, val);
//                    p_max = (std::max)(p_max, val);
//                }
//            }
//
//            std::stringstream qs;
//            qs << p_min << "\t" << p_max;
//            God::WriteLog("quant_info", qs.str());






            // dump all scores
//            WriteLogBestScores(Probs_, 12);

          mblas::Softmax(Probs_);
          Probs = blaze::forEach(Probs_, Log());
        }

        void Filter(const std::vector<size_t>& ids) {
          filtered_ = true;
          using namespace mblas;
          FilteredW4_ = Assemble<byColumn, Matrix>(w_.W4_, ids);
          FilteredB4_ = Assemble<byColumn, Matrix>(w_.B4_, ids);
        }

      private:
        const Weights& w_;
        bool filtered_;

        mblas::Matrix FilteredW4_;
        mblas::Matrix FilteredB4_;

        mblas::Matrix T1_;
        mblas::Matrix T2_;
        mblas::Matrix T3_;
        mblas::Matrix Probs_;

        static void WriteLogMatrix(mblas::ArrayMatrix mat) {
            size_t rows = mat.rows();
            size_t cols = mat.columns();
            std::stringstream ss;
            for (int j = 0; j < rows; ++j) {
                ss.str("   ");
                for (int i = 0; i < 4; ++i) {
                    ss << mat(j, i) << " ";
                }
                God::WriteLog("histogram_in", ss.str());
            }
        }

        static void WriteLogMatrixSize(mblas::ArrayMatrix mat, const char* label) {
            std::stringstream ss;
            ss << label << ": " << mat.rows() << " x " << mat.columns();
            God::WriteLog("histogram_in", ss.str());
            ss.str(std::string());
        }

        static void WriteLogAllScores(mblas::ArrayMatrix mat) {
            size_t rows = mat.rows();
            size_t cols = mat.columns();

            std::stringstream ss;
            ss.str(std::string());
            for (int i = 0; i < rows; ++i) {
                for (int j = 0; j < God::GetTargetVocab().size(); ++j) {
                    ss << j << "\t" << roundf(mat(i, j)*1000)/1000 << "\n";
                }
            }
            ss << "$$$$$";
            God::WriteLog("histogram_in" + God::randomStrGen(), ss.str());
        }

        static void WriteLogBestScores(mblas::ArrayMatrix mat, int beamSize) {
            size_t rows = mat.rows();
            size_t cols = mat.columns();

            std::stringstream ss;
            ss.str(std::string());
            for (int i = 0; i < rows; ++i) {
                std::priority_queue<std::pair<double, int>> q;
                for (int j = 0; j < God::GetTargetVocab().size(); ++j) {
                    q.push(std::pair<double, int>(mat(i, j), j));
                }

                int bsize = beamSize;
                if (q.size() < beamSize) {
                    bsize = q.size();
                }
                for (int b = 0; b < bsize; ++b) {
                    int ki = q.top().second;
                    ss << ki << "\t" << roundf(mat(i, ki)*1000)/1000 << "\n";
                    q.pop();
                }
            }
            ss << "$$$$$";
            God::WriteLog("histogram_in", ss.str());
        }

    };

  public:
    Decoder(const Weights& model)
    : embeddings_(model.decEmbeddings_),
      rnn1_(model.decInit_, model.decGru1_),
      rnn2_(model.decGru2_),
	  attention_(model.decAttention_),
      softmax_(model.decSoftmax_)
    {}

    void MakeStep(mblas::Matrix& NextState,
                  mblas::ArrayMatrix& Probs,
                  const mblas::Matrix& State,
                  const mblas::Matrix& Embeddings,
                  const mblas::Matrix& SourceContext) {
        boost::timer t1;
        GetHiddenState(HiddenState_, State, Embeddings);
        double elapsed_time1 = t1.elapsed();
        boost::timer t2;
        GetAlignedSourceContext(AlignedSourceContext_, HiddenState_, SourceContext);
        double elapsed_time2 = t2.elapsed();
        boost::timer t3;
        GetNextState(NextState, HiddenState_, AlignedSourceContext_);
        double elapsed_time3 = t3.elapsed();
        boost::timer t4;
        GetProbs(Probs, NextState, Embeddings, AlignedSourceContext_);
        double elapsed_time4 = t4.elapsed();

//        LOG(info) << "T: " << elapsed_time1 << " x " << elapsed_time2 << " x " << elapsed_time3 << " x " << elapsed_time4;
    }

    void EmptyState(mblas::Matrix& State,
                    const mblas::Matrix& SourceContext,
                    size_t batchSize = 1) {
      rnn1_.InitializeState(State, SourceContext, batchSize);
      attention_.Init(SourceContext);
    }

    void EmptyEmbedding(mblas::Matrix& Embedding,
                        size_t batchSize = 1) {
      Embedding.resize(batchSize, embeddings_.GetCols());
      Embedding = 0.0f;
    }

    void Lookup(mblas::Matrix& Embedding,
                const std::vector<size_t>& w) {
      embeddings_.Lookup(Embedding, w);
    }

    void Filter(const std::vector<size_t>& ids) {
      softmax_.Filter(ids);
    }

    void GetAttention(mblas::Matrix& attention) {
    	attention_.GetAttention(attention);
    }

    mblas::Matrix& GetAttention() {
      return attention_.GetAttention();
    }

    size_t GetVocabSize() const {
      return embeddings_.GetRows();
    }

  private:

    void GetHiddenState(mblas::Matrix& HiddenState,
                        const mblas::Matrix& PrevState,
                        const mblas::Matrix& Embedding) {
      rnn1_.GetNextState(HiddenState, PrevState, Embedding);
    }

    void GetAlignedSourceContext(mblas::Matrix& AlignedSourceContext,
                                 const mblas::Matrix& HiddenState,
                                 const mblas::Matrix& SourceContext) {
    	attention_.GetAlignedSourceContext(AlignedSourceContext, HiddenState, SourceContext);
    }

    void GetNextState(mblas::Matrix& State,
                      const mblas::Matrix& HiddenState,
                      const mblas::Matrix& AlignedSourceContext) {
      rnn2_.GetNextState(State, HiddenState, AlignedSourceContext);
    }


    void GetProbs(mblas::ArrayMatrix& Probs,
                  const mblas::Matrix& State,
                  const mblas::Matrix& Embedding,
                  const mblas::Matrix& AlignedSourceContext) {
      softmax_.GetProbs(Probs, State, Embedding, AlignedSourceContext);
    }

  private:
    mblas::Matrix HiddenState_;
    mblas::Matrix AlignedSourceContext_;

    Embeddings<Weights::Embeddings> embeddings_;
    RNNHidden<Weights::DecInit, Weights::GRU> rnn1_;
    RNNFinal<Weights::DecGRU2> rnn2_;
    Attention<Weights::DecAttention> attention_;
    Softmax<Weights::DecSoftmax> softmax_;
};

}
