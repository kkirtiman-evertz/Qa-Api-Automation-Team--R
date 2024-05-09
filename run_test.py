import argparse
import glob
import os
import sys

import pytest

# Global configuration variables
TESTS_DIRECTORY = "tests"
TEST_SUITE_PREFIX = "tests_"

test_suites = [x for x in os.listdir(TESTS_DIRECTORY)]


def run_with_pytest(test_modules):
    """
    Runs the pytest framework for the specified test modules.
    Args:
        test_modules (list): List of test module paths.
    Returns:
        None
    """
    exit_code = pytest.main(test_modules)
    sys.exit(exit_code)


def find_test_py_files(directory):
    """
    Finds and returns a list of test files in the specified directory.
    Args:
        directory (str): Directories to search for test files.
    Returns:
        List of file paths for all the test files in the directory.
    """
    pattern = f"{directory}/**/test_*.py"
    files = glob.glob(pattern, recursive=True)
    return files


def process_service_arguments(service_names):
    """
    Processes the service names arguments and generates a list of test module paths to be executed.
    Args:
        service_names (list): List of service names
    Returns:
        list: List of test module paths.
    """
    if not service_names or service_names[0] == "all_test_suits":
        return []

    test_modules = []
    for selected_test_suite in service_names:
        test_suite = f"{TEST_SUITE_PREFIX}{selected_test_suite}"
        if test_suite in test_suites:
            all_req_test_files = find_test_py_files(
                os.path.join(TESTS_DIRECTORY, test_suite)
            )
            test_modules.extend(all_req_test_files)
    return test_modules


def main():
    """
    Main function to handle command line arguments and execute tests.
    Returns:
        None
    """

    parser = argparse.ArgumentParser(
        description="Run all the tests or particular selected test cases"
    )
    parser.add_argument("--service", nargs="+", help="List of service names")
    parser.add_argument(
        "--config",
        default="api-tests-config.yaml",  # Default config file name
        help="Config file name",
    )
    args = parser.parse_args()
    service_names = args.service
    config_file = args.config

    os.environ["config"] = config_file

    test_modules = process_service_arguments(service_names)
    run_with_pytest(test_modules)


if __name__ == "__main__":
    main()
