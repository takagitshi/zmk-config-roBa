/* SPDX-License-Identifier: MIT */

#include <assert.h>
#include <limits.h>
#include <stdio.h>

#include <roba/gesture_state.h>

#define THRESHOLD 100
#define COOLDOWN_MS 150

static enum roba_gesture_direction update(struct roba_gesture_state *state,
                                           enum roba_gesture_axis axis, int32_t value,
                                           bool sync, int64_t now_ms) {
    return roba_gesture_state_update(state, axis, value, sync, now_ms, THRESHOLD,
                                     COOLDOWN_MS);
}

int main(void) {
    struct roba_gesture_state state;

    roba_gesture_state_reset(&state);
    assert(update(&state, ROBA_GESTURE_AXIS_X, 80, false, 1000) == ROBA_GESTURE_NONE);
    assert(update(&state, ROBA_GESTURE_AXIS_Y, 60, true, 1000) == ROBA_GESTURE_RIGHT);

    roba_gesture_state_reset(&state);
    assert(update(&state, ROBA_GESTURE_AXIS_X, -100, true, 1000) == ROBA_GESTURE_LEFT);

    roba_gesture_state_reset(&state);
    assert(update(&state, ROBA_GESTURE_AXIS_Y, -100, true, 1000) == ROBA_GESTURE_UP);

    roba_gesture_state_reset(&state);
    assert(update(&state, ROBA_GESTURE_AXIS_Y, 100, true, 1000) == ROBA_GESTURE_DOWN);
    assert(update(&state, ROBA_GESTURE_AXIS_X, 200, true, 1100) == ROBA_GESTURE_NONE);
    assert(update(&state, ROBA_GESTURE_AXIS_X, 100, true, 1165) == ROBA_GESTURE_NONE);
    assert(update(&state, ROBA_GESTURE_AXIS_X, 100, true, 1180) == ROBA_GESTURE_RIGHT);

    roba_gesture_state_reset(&state);
    assert(update(&state, ROBA_GESTURE_AXIS_X, INT32_MAX, false, 1000) == ROBA_GESTURE_NONE);
    assert(update(&state, ROBA_GESTURE_AXIS_X, 1, false, 1000) == ROBA_GESTURE_NONE);
    assert(state.x == INT32_MAX);

    puts("gesture_state_test: PASS");
    return 0;
}
