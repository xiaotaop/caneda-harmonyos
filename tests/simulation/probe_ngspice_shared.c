/*
 * Standalone libngspice smoke test. Run in an empty writable directory with
 * the RC fixture copied to rc-step.cir. See scripts/ohos/README.md.
 */
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include "sharedspice.h"

static int log_message(char *message, int instance, void *data)
{
    (void)instance;
    (void)data;
    fprintf(stderr, "%s\n", message);
    return 0;
}

static int controlled_exit(int status, bool immediate, bool quit, int instance, void *data)
{
    (void)immediate;
    (void)quit;
    (void)instance;
    *(bool *)data = true;
    fprintf(stderr, "ngspice requested exit with status %d\n", status);
    return 0;
}

static bool run_rc(char *write_command, bool *exited)
{
    char source[] = "source rc-step.cir";
    char run[] = "run";
    char time[] = "time";
    char voltage[] = "v(out)";
    if (ngSpice_Command(source) != 0 || *exited ||
        ngSpice_Command(run) != 0 || *exited) {
        return false;
    }

    const char *plot = ngSpice_CurPlot();
    pvector_info axis = ngGet_Vec_Info(time);
    if (!plot || strncmp(plot, "tran", 4) != 0 || !axis ||
        !axis->v_realdata || axis->v_length < 2) {
        return false;
    }
    // ngGet_Vec_Info reuses its result structure on each call.
    const int points = axis->v_length;
    pvector_info curve = ngGet_Vec_Info(voltage);
    if (!curve || !curve->v_realdata || curve->v_length != points) {
        return false;
    }

    printf("plot %s: %d points\n", plot, points);
    return ngSpice_Command(write_command) == 0 && !*exited;
}

int main(void)
{
    bool exited = false;
    char ascii[] = "set filetype=ascii";
    char write_first[] = "write rc-first.raw time v(out)";
    char write_second[] = "write rc-second.raw time v(out)";
    char clear_plots[] = "destroy all";
    char remove_circuit[] = "remcirc";
    if (ngSpice_Init(log_message, NULL, controlled_exit, NULL, NULL, NULL, &exited) != 0 ||
        exited || ngSpice_Command(ascii) != 0 || exited ||
        !run_rc(write_first, &exited) ||
        ngSpice_Command(clear_plots) != 0 || exited ||
        ngSpice_Command(remove_circuit) != 0 || exited ||
        !run_rc(write_second, &exited)) {
        fputs("libngspice RC probe failed\n", stderr);
        return 1;
    }
    return 0;
}
