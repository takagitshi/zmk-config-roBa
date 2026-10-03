if(CONFIG_SHIELD_ROBA_L OR CONFIG_SHIELD_ROBA_R)
  zephyr_library()
  zephyr_include_directories(${CMAKE_CURRENT_LIST_DIR}/include)
  zephyr_library_sources_ifdef(CONFIG_ZMK_BEHAVIOR_ENCODER_KEY_DIVIDER
    src/encoder_divider_state.c
    src/behavior_encoder_key_divider.c)
  zephyr_library_sources_ifdef(CONFIG_ZMK_INPUT_PROCESSOR_GESTURE
    src/gesture_state.c
    src/input_processor_gesture.c)
endif()
