from app.core.result import Result


def get_success_result() -> Result:
    result = Result()
    result.set_success()
    return result


def get_error_result() -> Result:
    result = Result()
    result.error('some error')
    return result


def get_failed_result() -> Result:
    return Result()
