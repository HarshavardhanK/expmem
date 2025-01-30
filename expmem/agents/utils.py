import signal
import traceback
from contextlib import contextmanager
from typing import Optional, Any, Callable


class TimeoutException(Exception):
    pass

@contextmanager
def timeout(seconds: int):
    """
    Context manager that raises TimeoutException if the contained code
    takes longer than specified seconds to execute.
    
    Args:
        seconds (int): Maximum number of seconds to allow execution
        
    Raises:
        TimeoutException: If execution time exceeds specified seconds
    """
    def timeout_handler(signum, frame):
        raise TimeoutException(f"Execution timed out after {seconds} seconds")

    # Set up the timeout handler
    previous_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Restore previous signal handler and alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)



from llm_sandbox import SandboxSession

session = SandboxSession(lang="python", keep_template=True)
session.open()

def execute_sample_ios(code, sample_io):
            # Capture stdout
        #old_stdout = sys.stdout
        #sys.stdout = StringIO()

    result = []
    error = []
    timeout = 5
    passed = False
    
    full_code = ""

    try:
        
        for sample in sample_io:
            
            full_code = ("from typing import *\n" if "from typing import *" not in code else "") + \
                code + "\n" + sample + "\n"
            
            print("Running full code: ", full_code)

            try:
                
                res = session.run(full_code)

                if 'Error' not in res.text:
                    result.append(f"Passed in test case: {sample}")
                    passed = True

                else:

                    error.append(f"Error in code for test case: {sample}, {res.text}")
                    print(f"Error in test case: {sample}, {res.text}")

            except Exception as e:
                error.append(f"Exeption in: {sample}")
                print("Execution timed out")

    except Exception as e:
        print(f"Exception {e}")
        error.append(f"Exception: {str(e)}\n\nTraceback:\n{traceback.format_exc()} in sample test case: {sample}")

    return passed, result, error, full_code
    

def execute_test_case(code, test_case, entry_point):

    result = []
    error = []
    timeout = 5
    full_code = ""
    
    passed = False

    try:

        full_code = ("from typing import *\n" if "from typing import *" not in code else "") + \
        code + "\n" + test_case + \
        "\n" + f"check({entry_point})"
                # Execute the code
        #print("Running full code: ", full_code)

        try:
                # function_with_timeout(
                #     exec,
                #     (code, globals()),
                #     timeout
                # )
                #exec_with_timeout(full_code, timeout_secs=2)
            res = session.run(full_code)

            if 'Error' not in res.text:
                result.append(f"Passed in test case: {test_case}")
                passed = True

            else:

                error.append(f"Error in code for test case: {test_case}, {res.text}")
                print(f"Error in test case: {test_case}, {res.text}")

        except TimeoutException:
            error.append(f"Exception in test case: {test_case}")
            print("Execution timed out")

    except Exception as e:
        print(f"Exception {e}")
        error.append(f"Exception: {str(e)}\n\nTraceback:\n{traceback.format_exc()} in test case: {test_case}")

    return passed, result, error, full_code


def close_session():
    session.close()