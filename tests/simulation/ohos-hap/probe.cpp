// Fixed-input D3 probe. This module is only built into the test HAP.
#include <napi/native_api.h>
#include <cerrno>
#include <cstdlib>
#include <fcntl.h>
#include <string>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>
#include "sharedspice.h"

namespace {

struct ChildFailure {
    int phase;
    int error;
};

[[noreturn]] void reportFailure(int fd, int phase)
{
    const ChildFailure failure{phase, errno};
    (void)write(fd, &failure, sizeof(failure));
    _exit(127);
}

std::string runCli(const std::string &dir)
{
    std::string program = dir + "/ngspice";
    if (chmod(program.c_str(), 0700) != 0)
        return "chmod errno=" + std::to_string(errno);

    int report[2];
    if (pipe2(report, O_CLOEXEC) != 0)
        return "pipe errno=" + std::to_string(errno);

    char *args[] = {program.data(), const_cast<char *>("-n"), const_cast<char *>("-b"),
                    const_cast<char *>("-r"), const_cast<char *>("cli.raw"),
                    const_cast<char *>("rc-step.cir"), nullptr};
    char ascii[] = "SPICE_ASCIIRAWFILE=1";
    char locale[] = "LC_ALL=C";
    char *env[] = {ascii, locale, nullptr};
    const char *workingDirectory = dir.c_str();
    pid_t pid = fork();
    if (pid == 0) {
        close(report[0]);
        if (chdir(workingDirectory) != 0)
            reportFailure(report[1], 0);
        int log = open("cli.log", O_CREAT | O_EXCL | O_WRONLY, 0600);
        if (log < 0)
            reportFailure(report[1], 1);
        if (dup2(log, STDOUT_FILENO) < 0 || dup2(log, STDERR_FILENO) < 0)
            reportFailure(report[1], 2);
        if (log > STDERR_FILENO)
            close(log);
        execve(args[0], args, env);
        reportFailure(report[1], 3);
    }
    const int forkError = errno;
    close(report[1]);
    if (pid < 0) {
        close(report[0]);
        return "fork errno=" + std::to_string(forkError);
    }

    ChildFailure failure{};
    ssize_t bytes;
    do {
        bytes = read(report[0], &failure, sizeof(failure));
    } while (bytes < 0 && errno == EINTR);
    close(report[0]);
    int status = 0;
    pid_t finished;
    do {
        finished = waitpid(pid, &status, 0);
    } while (finished < 0 && errno == EINTR);
    if (finished < 0 || bytes < 0)
        return "child status unavailable";
    if (bytes == sizeof(failure)) {
        const char *phases[] = {"chdir", "open log", "redirect log", "execve"};
        return std::string(phases[failure.phase]) + " errno=" + std::to_string(failure.error);
    }
    if (WIFEXITED(status))
        return "exit=" + std::to_string(WEXITSTATUS(status));
    return "signal=" + std::to_string(WTERMSIG(status));
}

bool spiceExit = false;
int controlledExit(int, bool, bool, int, void *)
{
    spiceExit = true;
    return 0;
}

std::string runShared(const std::string &dir, const char *output)
{
    static bool initialized = false;
    if (!initialized) {
        spiceExit = false;
        if (ngSpice_Init(nullptr, nullptr, controlledExit, nullptr, nullptr,
                         nullptr, nullptr) != 0 || spiceExit)
            return "init failed";
        initialized = true;
    }
    char destroy[] = "destroy all";
    char remove[] = "remcirc";
    char ascii[] = "set filetype=ascii";
    char run[] = "run";
    char axisName[] = "time";
    char voltageName[] = "v(out)";
    (void)ngSpice_Command(destroy);
    (void)ngSpice_Command(remove);
    std::string source = "source " + dir + "/rc-step.cir";
    if (ngSpice_Command(ascii) || ngSpice_Command(source.data()) ||
        ngSpice_Command(run) || spiceExit)
        return "simulation failed";

    pvector_info axis = ngGet_Vec_Info(axisName);
    if (!axis || !axis->v_realdata || axis->v_length < 2)
        return "missing time axis";
    const int points = axis->v_length;
    // ngGet_Vec_Info reuses the descriptor, so save the length first.
    pvector_info voltage = ngGet_Vec_Info(voltageName);
    if (!voltage || !voltage->v_realdata || voltage->v_length != points)
        return "missing voltage";
    const std::string rawPath = dir + "/" + output;
    std::string write = "write " + rawPath + " time v(out)";
    if (ngSpice_Command(write.data()) || spiceExit || access(rawPath.c_str(), R_OK) != 0)
        return "RAW write failed";
    return "points=" + std::to_string(points);
}

napi_value runProbe(napi_env env, napi_callback_info info)
{
    size_t argc = 1;
    napi_value argument;
    char path[1024];
    size_t length = 0;
    if (napi_get_cb_info(env, info, &argc, &argument, nullptr, nullptr) != napi_ok ||
        argc != 1 || napi_get_value_string_utf8(env, argument, path, sizeof(path), &length) != napi_ok ||
        length == 0 || length >= sizeof(path) - 1 ||
        std::string(path, length).find_first_not_of(
            "/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-") != std::string::npos) {
        napi_throw_type_error(env, nullptr, "expected a private probe directory");
        return nullptr;
    }

    const std::string dir(path, length);
    const std::string cli = runCli(dir);
    const std::string first = runShared(dir, "shared.raw");
    const std::string repeat = runShared(dir, "shared-repeat.raw");
    const std::string summary = "cli=" + cli + "; shared=" + first + "; repeat=" + repeat;
    napi_value result;
    napi_create_string_utf8(env, summary.c_str(), summary.size(), &result);
    return result;
}

napi_value initialize(napi_env env, napi_value exports)
{
    napi_property_descriptor function = {
        "run", nullptr, runProbe, nullptr, nullptr, nullptr, napi_default, nullptr
    };
    napi_define_properties(env, exports, 1, &function);
    return exports;
}

napi_module module = {
    1, 0, nullptr, initialize, "ngspice_probe", nullptr, {nullptr}
};

} // namespace

extern "C" __attribute__((constructor)) void registerNgspiceProbe()
{
    napi_module_register(&module);
}
