import logging
import os
import pwd
import subprocess
import threading
import time

from app.core.files import load_config
from app.core.result import Result

logger = logging.getLogger('logsmith')

def get_login_shell():
    return os.environ.get("SHELL") or pwd.getpwuid(os.getuid()).pw_shell or "/bin/sh"

def login_shell_env(path_extension=None):
    shell = get_login_shell()
    cmd = [shell, "-l", "-c", "printenv"]
    out = subprocess.check_output(cmd).decode()
    env = {}
    for kv in out.split("\n"):
        if not kv:
            continue
        k, _, v = kv.partition("=")
        env[k] = v
    if path_extension:
        original_path = env['PATH']
        env['PATH'] = f'{path_extension}:{original_path}'
    return env

def run(command, timeout=5) -> Result:
    logger.info(f"run command: {command}")
    shell = get_login_shell()
    logger.info(f"shell: {shell}")

    config = load_config()
    path_extension = config.get("shell_path_extension", None)

    result = Result()
    proc = None
    lines: list[str] = []

    def reader(stream):
        # Runs in a thread: log output as soon as it arrives, collect it too.
        for line in iter(stream.readline, ""):
            line = line.rstrip("\n")
            lines.append(line)
            logger.info(line)
        stream.close()

    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # merge stderr into stdout (avoids deadlocks)
            shell=True,
            text=True,
            bufsize=1,
            executable=shell,
            env=login_shell_env(path_extension),
        )

        assert proc.stdout is not None
        t = threading.Thread(target=reader, args=(proc.stdout,), daemon=True)
        t.start()
        proc.wait(timeout=timeout)
        t.join(timeout=1)

        if proc.returncode == 0:
            result.add_payload("\n".join(lines))
            result.set_success()
        else:
            result.error(f"command {command} failed (exit {proc.returncode})")

    except subprocess.TimeoutExpired:
        msg = f"command {command} took too long and was aborted"
        logger.warning(msg)

        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)

        result.error(msg)

    except FileNotFoundError:
        msg = f"command {command} not found"
        logger.warning(msg)
        result.error(msg)

    except subprocess.CalledProcessError:
        msg = f"command {command} failed"
        logger.warning(msg, exc_info=True)
        result.error(msg)

    except Exception as error:
        msg = f"command {command} failed with unknown error"
        logger.error(msg)
        logger.error(str(error), exc_info=True)
        result.error(msg)

    return result
