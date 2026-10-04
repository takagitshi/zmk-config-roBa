# Zephyr 3.5 loads module extensions before Devicetree preprocessing.
if(SHIELD MATCHES "(^|[ ;])roBa_[LR]($|[ ;])")
  if(NOT KEYMAP_FILE)
    message(FATAL_ERROR "roBa AML generation requires a selected KEYMAP_FILE")
  endif()
  set(roba_aml_keymap "${KEYMAP_FILE}")
  set(roba_aml_generator "${CMAKE_CURRENT_LIST_DIR}/../scripts/generate-aml-exclusions.py")
  set(roba_aml_header "${CMAKE_BINARY_DIR}/aml-exclusions.h")
  set(roba_aml_depfile "${CMAKE_BINARY_DIR}/aml-exclusions.inputs")
  execute_process(
    COMMAND "${PYTHON_EXECUTABLE}" "${roba_aml_generator}" "${roba_aml_keymap}" "${roba_aml_header}" --mouse-layer 1 --key-count 43 --depfile "${roba_aml_depfile}"
    RESULT_VARIABLE roba_aml_result
    ERROR_VARIABLE roba_aml_error
  )
  if(NOT roba_aml_result EQUAL 0)
    message(FATAL_ERROR "roBa AML generation failed: ${roba_aml_error}")
  endif()
  file(STRINGS "${roba_aml_depfile}" roba_aml_inputs)
  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    ${roba_aml_inputs} "${roba_aml_generator}"
    "${CMAKE_CURRENT_LIST_DIR}/../scripts/aml_keymap.py")
  list(APPEND DTS_EXTRA_CPPFLAGS "-I${CMAKE_BINARY_DIR}")
endif()
