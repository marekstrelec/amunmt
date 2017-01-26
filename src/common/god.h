#pragma once
#include <memory>
#include <iostream>

#include "common/config.h"
#include "common/loader.h"
#include "common/logging.h"
#include "common/scorer.h"
#include "common/types.h"
#include "common/processor/processor.h"

#include "3rd_party/spdlog/sinks/file_sinks.h"
#include "common/vocab.h"

class Weights;
class Vocab;
class Filter;
class InputFileStream;

class God {
  public:
    virtual ~God();

    static God& Init(const std::string&);
    static God& Init(int argc, char** argv);

    static God& Summon() {
      return instance_;
    }

    static bool Has(const std::string& key) {
      return Summon().config_.Has(key);
    }

    template <typename T>
    static T Get(const std::string& key) {
      return Summon().config_.Get<T>(key);
    }

    static YAML::Node Get(const std::string& key) {
      return Summon().config_.Get(key);
    }

    static Vocab& GetSourceVocab(size_t i = 0);
    static Vocab& GetTargetVocab();

    static std::istream& GetInputStream();

    static Filter& GetFilter();

    static std::vector<ScorerPtr> GetScorers(size_t);
    static std::vector<std::string> GetScorerNames();
    static std::map<std::string, float>& GetScorerWeights();

    static std::vector<std::string> Preprocess(size_t i, const std::vector<std::string>& input);
    static std::vector<std::string> Postprocess(const std::vector<std::string>& input);

    static void CleanUp();

    void LoadWeights(const std::string& path);

    static void OutputVocab() {
        std::stringstream ss;
        for (int i = 0; i < GetTargetVocab().size(); ++i) {
//            if (i == 3349 || i == 3448) // { and } characters are not friends with spdlog
//                continue;

            ss.str(std::string());
            ss << i <<  "\t" << GetTargetVocab().operator[](i);

            try {
                God::WriteLog("vocab_words", ss.str());
            } catch (const std::exception& e) {
                ss.str(std::string());
                ss << i << " ERROR";
                God::WriteLog("vocab_words", ss.str());
            }
        }
    }

    static void WriteLog(std::string filename, std::string text) {
        auto sink = std::make_shared<spdlog::sinks::rotating_file_sink_st>("out/" + filename, "out", 1048576 * 1000, 5000);
        auto histolog = std::make_shared<spdlog::logger>(filename, sink);
        histolog->set_pattern("%v");

        histolog->info() << text;

    }

  private:
    God& NonStaticInit(int argc, char** argv);

    void LoadScorers();
    void LoadFiltering();
    void LoadPrePostProcessing();

    static God instance_;
    Config config_;

    std::vector<std::unique_ptr<Vocab>> sourceVocabs_;
    std::unique_ptr<Vocab> targetVocab_;

    std::unique_ptr<Filter> filter_;

    std::vector<std::vector<PreprocessorPtr>> preprocessors_;
    std::vector<PostprocessorPtr> postprocessors_;

    std::map<std::string, LoaderPtr> cpuLoaders_;
    std::map<std::string, LoaderPtr> gpuLoaders_;
    std::map<std::string, float> weights_;

    std::shared_ptr<spdlog::logger> info_;
    std::shared_ptr<spdlog::logger> progress_;

    std::unique_ptr<InputFileStream> inputStream_;

};
