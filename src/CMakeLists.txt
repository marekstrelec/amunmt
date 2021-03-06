
include_directories(.)
include_directories(3rd_party)

add_library(cpumode OBJECT
  cpu/mblas/matrix.cpp
  cpu/mblas/phoenix_functions.cpp
  cpu/dl4mt/decoder.cpp
  cpu/dl4mt/encoder.cpp
  cpu/dl4mt/gru.cpp
  cpu/dl4mt/model.cpp
  cpu/decoder/encoder_decoder.cpp
)

add_library(libcommon OBJECT
  common/config.cpp
  common/exception.cpp
  common/filter.cpp
  common/god.cpp
  common/history.cpp
  common/loader.cpp
  common/logging.cpp
  common/printer.cpp
  common/scorer.cpp
  common/search.cpp
  common/sentence.cpp
  common/processor/bpe.cpp
  common/utils.cpp
  common/vocab.cpp
)

if(CUDA_FOUND)

set_source_files_properties( common/loader_factory.cpp
  PROPERTIES CUDA_SOURCE_PROPERTY_FORMAT OBJ )

cuda_add_executable(
  amun
  common/decoder_main.cpp
  gpu/decoder/ape_penalty.cu
  gpu/decoder/encoder_decoder.cu
  gpu/dl4mt/encoder.cu
  gpu/dl4mt/gru.cu
  gpu/mblas/matrix.cu
  gpu/npz_converter.cu
  common/loader_factory.cpp
  $<TARGET_OBJECTS:libcommon>
  $<TARGET_OBJECTS:cpumode>
  $<TARGET_OBJECTS:libyaml-cpp>
  $<TARGET_OBJECTS:libcnpy>
)

cuda_add_library(amunmt SHARED
  python/amunmt.cpp
  gpu/decoder/ape_penalty.cu
  gpu/decoder/encoder_decoder.cu
  gpu/mblas/matrix.cu
  gpu/dl4mt/encoder.cu
  gpu/dl4mt/gru.cu
  gpu/npz_converter.cu
  common/loader_factory.cpp
  $<TARGET_OBJECTS:libcommon>
  $<TARGET_OBJECTS:libcnpy>
  $<TARGET_OBJECTS:cpumode>
  $<TARGET_OBJECTS:libyaml-cpp>
)

#cuda_add_executable(
#  nth
#  gpu/nth_benchmark.cu
#  gpu/mblas/matrix.cu
#  $<TARGET_OBJECTS:libcommon>
#  $<TARGET_OBJECTS:libcnpy>
#  $<TARGET_OBJECTS:cpumode>
#  $<TARGET_OBJECTS:libyaml-cpp>
#)


else(CUDA_FOUND)

add_executable(
  amun
  common/decoder_main.cpp
  common/loader_factory.cpp
  $<TARGET_OBJECTS:libcnpy>
  $<TARGET_OBJECTS:cpumode>
  $<TARGET_OBJECTS:libcommon>
  $<TARGET_OBJECTS:libyaml-cpp>
)

add_library(amunmt SHARED
  python/amunmt.cpp
  common/loader_factory.cpp
  $<TARGET_OBJECTS:libcnpy>
  $<TARGET_OBJECTS:cpumode>
  $<TARGET_OBJECTS:libcommon>
  $<TARGET_OBJECTS:libyaml-cpp>
)
endif(CUDA_FOUND)


foreach(exec amun amunmt)
  if(CUDA_FOUND)
    target_link_libraries(${exec} ${EXT_LIBS} cuda)
    cuda_add_cublas_to_target(${exec})
  else(CUDA_FOUND)
    target_link_libraries(${exec} ${EXT_LIBS})
  endif(CUDA_FOUND)
  set_target_properties(${exec} PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
endforeach(exec)

add_subdirectory(3rd_party)
