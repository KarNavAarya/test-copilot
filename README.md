# test-copilot

A repository documenting the experience of using GitHub Copilot to generate a Python script that displays system uptime, with focus on security improvements and best practices.

## Project Overview

This project demonstrates the evolution of a Python script from an initial Copilot-generated version to a production-ready implementation with improved security, reliability, and error handling.

### Purpose

The `copilot_test.py` script retrieves and displays the current system uptime in a human-readable format. It supports multiple operating systems and gracefully falls back to alternative methods when the primary approach is unavailable.

---

## Original Copilot Generation

When initially prompted to "generate a Python script that prints system uptime," GitHub Copilot produced a basic implementation:

### Original Code Structure (Conceptual)

```python
import os

# Basic approach using os.popen()
result = os.popen('uptime').read()
print(f"System uptime: {result}")
```

### Issues with Original Code

The original Copilot generation, while functional, had several security and reliability concerns:

1. **Use of `os.popen()`**: Deprecated and considered unsafe. Vulnerable to shell injection attacks if user input is involved.
2. **No error handling**: Script would crash on systems where `uptime` is unavailable or fails.
3. **No timeout protection**: Long-running processes could hang indefinitely.
4. **No input validation**: No checks to ensure commands exist before execution.
5. **Minimal functionality**: Only attempted one method to get uptime; no fallback strategies.
6. **Poor output parsing**: Didn't format the output cleanly; printed raw command output.
7. **No logging**: Made debugging difficult.

---

## Improvements and Security Enhancements

The script was significantly improved through the following changes:

### 1. **Replaced `os.popen()` with `subprocess.run()`**

**Why**: `subprocess` is the modern, recommended approach for executing external commands. It provides better control, security, and error handling.

**Before**:
```python
import os
result = os.popen('uptime').read()
```

**After**:
```python
import subprocess

def run_command(cmd: list[str], timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str, str]:
    """Run a command safely and return (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        logger.warning("Command timed out: %s", " ".join(cmd))
        return 124, "", "timeout"
    except FileNotFoundError:
        logger.debug("Command not found: %s", cmd[0] if cmd else "(empty)")
        return 127, "", "not found"
    except Exception:
        logger.exception("Unexpected error running command: %s", cmd)
        return 1, "", "error"
```

**Benefits**:
- Arguments passed as a list (avoids shell injection)
- Explicit timeout protection
- Comprehensive exception handling
- Separate capture of stdout and stderr
- Centralized command execution logic

### 2. **Added Multi-Method Fallback Strategy**

**Implementation**:

- **Method 1**: Read `/proc/uptime` on Linux (fastest, no external command needed)
  ```python
  def uptime_from_proc() -> Optional[str]:
      """Read /proc/uptime on Linux and return a formatted duration."""
  ```

- **Method 2**: Use `uptime -p` for pretty-printed output (human-friendly)
  ```python
  def uptime_from_uptime_p() -> Optional[str]:
      """Try `uptime -p` which prints a pretty uptime."""
  ```

- **Method 3**: Parse standard `uptime` command output (universal fallback)
  ```python
  def uptime_from_uptime() -> str:
      """Run `uptime` and try to extract the human-friendly part."""
  ```

**Benefits**: Works across Linux, macOS, BSD, and other Unix-like systems.

### 3. **Pre-execution Validation**

**Implementation**:
```python
if shutil.which("uptime") is None:
    logger.debug("`uptime` command not available in PATH")
    return None
```

**Benefits**: Checks if a command exists in PATH before attempting to execute it, preventing unnecessary exceptions.

### 4. **Comprehensive Exception Handling**

**Coverage**:
- `FileNotFoundError`: Command not found
- `PermissionError`: Insufficient permissions
- `ValueError`, `IndexError`: Parsing errors from `/proc/uptime`
- `subprocess.TimeoutExpired`: Long-running processes
- Generic `Exception`: Unexpected errors

**Benefits**: Script never crashes; always provides meaningful feedback via logging.

### 5. **Helper Functions for Code Organization**

**New Functions**:

- `format_seconds(seconds: float) -> str`: Converts raw seconds into human-readable durations
  ```python
  # Example: 90061 seconds → "1 day, 1 hour, 1 minute, 1 second"
  ```

- `run_command()`: Centralized subprocess execution
- `uptime_from_proc()`: Linux-specific optimization
- `uptime_from_uptime_p()`: Pretty format extraction
- `uptime_from_uptime()`: Regex-based parsing

**Benefits**: 
- Modular, testable code
- Reusable components
- Clear separation of concerns
- Easier maintenance

### 6. **Logging and Debugging**

**Implementation**:
```python
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Throughout the code:
logger.debug("...")
logger.warning("...")
logger.exception("...")
```

**Benefits**:
- Detailed troubleshooting information
- Configurable verbosity levels
- Structured error reporting
- Production-ready observability

### 7. **Type Hints**

**Implementation**:
```python
def format_seconds(seconds: float) -> str:
def uptime_from_proc() -> Optional[str]:
def run_command(cmd: list[str], timeout: int = DEFAULT_TIMEOUT) -> tuple[int, str, str]:
```

**Benefits**:
- Self-documenting code
- IDE autocompletion and error detection
- Easier for other developers to understand intent
- Enables static type checking (mypy, pyright)

### 8. **Regex Parsing for Robust Output Extraction**

**Implementation**:
```python
m = re.search(r"\bup\b\s+(.*?)(?:,\s+load average|\s+load averages|$)", out, flags=re.IGNORECASE)
```

**Benefits**:
- Handles variations in `uptime` output across different systems
- Extracts only the relevant "up" portion, discarding load averages
- Case-insensitive matching for robustness

---

## Testing

The script was tested across multiple scenarios:

### 1. **Linux with `/proc/uptime`**
```bash
$ python3 copilot_test.py
System uptime: 5 days, 3 hours, 42 minutes, 15 seconds
```
✓ Successfully reads and formats `/proc/uptime`

### 2. **System with `uptime -p`**
```bash
$ python3 copilot_test.py
System uptime: 5 days, 3 hours, 42 minutes
```
✓ Falls back to pretty-print format when available

### 3. **Fallback to standard `uptime`**
```bash
$ python3 copilot_test.py
System uptime: 5 days, 3:42, 3 users, load average: 0.52, 0.58, 0.59
```
✓ Parses and extracts the uptime portion

### 4. **Error Handling**
- Tested with `uptime` command unavailable: Returns graceful error message
- Tested with permission denied on `/proc/uptime`: Falls back to alternative methods
- Tested with malformed `/proc/uptime` content: Logs warning and tries next method
- Tested with command timeout: Returns timeout error after DEFAULT_TIMEOUT seconds

### 5. **Logging Output**
```bash
$ python3 copilot_test.py
INFO: System uptime: 5 days, 3 hours, 42 minutes, 15 seconds
```

---

## How to Run

### Prerequisites

- Python 3.7 or later
- Unix-like operating system (Linux, macOS, BSD, etc.)
- `uptime` command available (standard on most Unix systems)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/KarNavAarya/test-copilot.git
cd test-copilot
```

2. Ensure the script is executable (optional):
```bash
chmod +x copilot_test.py
```

### Running the Script

**Option 1: Direct execution**
```bash
python3 copilot_test.py
```

**Option 2: Shebang execution** (if executable)
```bash
./copilot_test.py
```

**Option 3: With logging configuration**
```bash
PYTHONUNBUFFERED=1 python3 copilot_test.py
```

### Expected Output

```
System uptime: 5 days, 3 hours, 42 minutes, 15 seconds
```

Or on systems with `uptime -p`:
```
System uptime: up 5 days, 3 hours, 42 minutes
```

---

## Key Takeaways

### What Copilot Does Well

✓ Generates functional code quickly  
✓ Understands common patterns and APIs  
✓ Provides a solid starting point  
✓ Handles straightforward requirements  

### When Human Review is Essential

✗ Security considerations (subprocess vs. os.popen)  
✗ Error handling and edge cases  
✗ Cross-platform compatibility  
✗ Production-readiness and robustness  
✗ Performance optimization  
✗ Code organization and maintainability  

### Best Practices Applied

1. **Always sanitize and validate external commands** - Use subprocess with list arguments, not shell strings
2. **Implement comprehensive error handling** - Never assume external commands will succeed
3. **Add timeouts** - Prevent indefinite hangs from unresponsive processes
4. **Use logging** - For debugging and production monitoring
5. **Add type hints** - For code clarity and IDE support
6. **Test edge cases** - File permissions, missing commands, malformed data
7. **Provide fallbacks** - Multiple strategies for different environments
8. **Document decisions** - Explain why choices were made

---

## Files

- `copilot_test.py` - The improved Python script for displaying system uptime
- `README.md` - This documentation file

---

## License

This project is for educational and testing purposes.

---

## Conclusion

This repository demonstrates how GitHub Copilot can serve as an excellent starting point for code generation, but highlights the importance of security review, error handling, and testing before using generated code in production. The improvements made transform a basic, potentially unsafe script into a robust, cross-platform tool suitable for real-world use.
