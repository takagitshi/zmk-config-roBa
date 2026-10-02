/* SPDX-License-Identifier: MIT */

#pragma once

#include <stdbool.h>
#include <stdint.h>

enum roba_gesture_direction {
    ROBA_GESTURE_NONE,
    ROBA_GESTURE_LEFT,
    ROBA_GESTURE_RIGHT,
    ROBA_GESTURE_UP,
    ROBA_GESTURE_DOWN,
};

enum roba_gesture_axis {
    ROBA_GESTURE_AXIS_X,
    ROBA_GESTURE_AXIS_Y,
};

struct roba_gesture_state {
    int32_t x;
    int32_t y;
    int64_t cooldown_until_ms;
    bool cooling_down;
};

void roba_gesture_state_reset(struct roba_gesture_state *state);

enum roba_gesture_direction
roba_gesture_state_update(struct roba_gesture_state *state, enum roba_gesture_axis axis,
                          int32_t value, bool sync, int64_t now_ms, uint32_t threshold,
                          uint32_t cooldown_ms);
