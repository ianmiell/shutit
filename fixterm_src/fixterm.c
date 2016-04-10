#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <termio.h>
#include <termios.h>
#include <string.h>

#define BUFFER_SIZE (32)
#define NUM_PARAMS (5)

struct termio old_term;

void set_raw() {
    struct termio new_term;
    if (ioctl(1, TCGETA, &old_term) == -1) {
        exit(10);
    }
    memcpy(&new_term, &old_term, sizeof(struct termio));
    new_term.c_lflag &= ~(ICANON|ECHO|ECHOE|ECHOK|ECHONL);
    new_term.c_cc[VMIN] = 0;
    new_term.c_cc[VTIME] = 0;
    if (ioctl(1, TCSETA, &new_term) == -1) {
        exit(11);
    }
}

void set_cooked() {
    if (ioctl(1, TCSETA, &old_term) == -1) {
        exit(12);
    }
}

void set_window_size(int w, int h) {
    struct winsize ws;
    if (ioctl(1, TIOCGWINSZ, &ws) == -1) {
        set_cooked();
        exit(13);
    }
    ws.ws_col = w;
    ws.ws_row = h;
    if (ioctl(1, TIOCSWINSZ, &ws) == -1) {
        set_cooked();
        exit(14);
    }
}
void handle_alarm(int x) {
    set_cooked();
    exit(2);
}
void handle_abort(int x) {
    set_cooked();
    exit(3);
}
int main(int argc, char **argv) {
    int state = 0;
    int eof_count = 0;
    char buffer[BUFFER_SIZE];
    char *bp = buffer;
    char *param_start = buffer;
    int params[NUM_PARAMS];
    int param_index = 0;
    int i;
    for (i=0; i<NUM_PARAMS; i++) {
        params[i] = 0;
    }
    set_raw();
    signal(SIGALRM, handle_alarm);
    signal(SIGINT, handle_abort);
    signal(SIGTERM, handle_abort);
    alarm(1);
    printf("\33[18t");
    while (1) {
        int c = getchar();
        if (c == EOF) {
            eof_count++;
            if (eof_count > 20) {
                goto parse_error;
            } else {
                usleep(50000);
            }
            continue;
        }
        *bp = c;
        bp++;
        switch (state) {
        case 0:
            if (c == 27) {
                state = 1;
                continue;
            } else {
                goto parse_error;
            }
            break;
        case 1:
            if (c == '[') {
                state = 2;
                param_start = bp;
                continue;
            } else {
                goto parse_error;
            }
            break;
        case 2:
            if (c == 't') {
                state = 3;
            }
            if (bp >= (buffer + BUFFER_SIZE - 1)) {
                goto parse_error;
            }

            if (c == ';') {
                if (param_index >= NUM_PARAMS) {
                    goto parse_error;
                }
                params[param_index] = atoi(param_start);
                param_start=bp;
                param_index++;
            }
            break;
        }
        if (state == 3) { break; }
    }
    *bp = '\0';
    if (param_index >= NUM_PARAMS) {
        goto parse_error;
    }
    params[param_index] = atoi(param_start);
    param_start=bp;
    param_index++;
    int width, height;
    if (param_index == 2) {
        height = params[0];
        width = params[1];
    } else if ((param_index == 3) && (params[0] == 8)) {
        height = params[1];
        width = params[2];
    } else {
        set_cooked();
        exit(13);
    }
    set_window_size(width, height);
    set_cooked();
    exit(0);
parse_error:
    set_cooked();
    exit(1);
}
