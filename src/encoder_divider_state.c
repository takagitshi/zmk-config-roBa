/*
 * Copyright (c) 2026 Takashi Imai
 *
 * SPDX-License-Identifier: MIT
 */

#include <roba/encoder_divider_state.h>

void roba_encoder_divider_state_reset(struct roba_encoder_divider_state *state) {
    state->direction = 0;
    state->count = 0;
    state->last_input_ms = 0;
    state->has_direction = false;
}

bool roba_encoder_divider_state_update(struct roba_encoder_divider_state *state,
                                       uint32_t direction, uint32_t divisor, int64_t now_ms,
                                       uint32_t timeout_ms) {
    if (divisor == 0) {
        roba_encoder_divider_state_reset(state);
        return false;
    }

    if (!state->has_direction || state->direction != direction || now_ms < state->last_input_ms ||
        (now_ms - state->last_input_ms) > timeout_ms) {
        state->direction = direction;
        state->count = 1;
        state->last_input_ms = now_ms;
        state->has_direction = true;

        if (divisor == 1) {
            roba_encoder_divider_state_reset(state);
            return true;
        }

        return false;
    }

    state->last_input_ms = now_ms;
    state->count++;
    if (state->count < divisor) {
        return false;
    }

    roba_encoder_divider_state_reset(state);
    return true;
}
