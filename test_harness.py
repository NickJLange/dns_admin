import requests
import time

# Configuration
BASE_URL = "http://localhost:19000"
# Define endpoints to test.
# Using placeholder values for parameters where the goal is to hit the endpoint,
# not necessarily to get a successful data response from the business logic.
# The session management code should be exercised regardless.
ENDPOINTS = [
    "/pihole/alldns/",
    "/pihole/status/test_domain_block",  # Placeholder for a domain group
    "/pihole/status_all/",
    "/pihole/enable_all/",
    "/pihole/disable_all/",
    "/ubiquiti/status_rule/test_rule",  # Placeholder for a firewall rule name
    "/ubiquiti/status_device/test_device",  # Placeholder for a device name/group
    "/ubiquiti/refresh",
    # Add more specific endpoints if needed to test different scenarios
    # For example, if some rules/devices are known to exist in a test environment:
    # "/ubiquiti/status_rule/KnownRuleName",
    # "/pihole/status/KnownDomainGroup",
]
ITERATIONS = 1000  # Number of times to loop through all endpoints
# ITERATIONS = 10 # For quicker testing during development
DURATION_MINUTES = 0.5 # Set to 0 to use ITERATIONS, otherwise loop for this duration
REQUEST_DELAY_SECONDS = 0.1  # Delay between individual requests

def run_test_harness():
    """Runs the test harness to hit defined API endpoints."""
    print("Starting API test harness...")

    start_time = time.time()
    endpoints_hit = 0
    errors_encountered = 0

    if DURATION_MINUTES > 0:
        loop_condition = lambda: (time.time() - start_time) < (DURATION_MINUTES * 60)
        print(f"Will run for approximately {DURATION_MINUTES} minutes.")
    else:
        iteration_count = 0
        loop_condition = lambda: iteration_count < ITERATIONS
        print(f"Will run for {ITERATIONS} iterations through all endpoints.")

    try:
        while loop_condition():
            if DURATION_MINUTES <= 0:
                # Only increment iteration_count if not duration-based
                # For duration-based, this would be an inner loop counter if needed
                # but the current structure iterates through endpoints per outer loop check.
                # This means a duration based test will make many more requests than an iteration based one.
                # Let's adjust to make it more comparable.
                pass


            for endpoint in ENDPOINTS:
                full_url = BASE_URL + endpoint
                try:
                    response = requests.get(full_url, timeout=10)
                    print(f"GET {full_url} - Status: {response.status_code}")
                    endpoints_hit += 1
                except requests.exceptions.ConnectionError as e:
                    print(f"GET {full_url} - Connection Error: {e}")
                    errors_encountered += 1
                except requests.exceptions.Timeout as e:
                    print(f"GET {full_url} - Timeout Error: {e}")
                    errors_encountered += 1
                except requests.exceptions.RequestException as e:
                    print(f"GET {full_url} - Error: {e}")
                    errors_encountered += 1

                time.sleep(REQUEST_DELAY_SECONDS)

            if DURATION_MINUTES <= 0:
                # iteration_count is only used if not duration based
                # to avoid confusion, this variable is only for iteration based tests
                nonlocal iteration_count # type: ignore
                iteration_count +=1


    except KeyboardInterrupt:
        print("\nTest harness interrupted by user.")
    finally:
        end_time = time.time()
        total_time_seconds = end_time - start_time
        print(f"\nTest harness finished.")
        print(f"Total execution time: {total_time_seconds:.2f} seconds.")
        print(f"Total endpoints hit successfully (ignoring business logic errors): {endpoints_hit}")
        print(f"Total errors (connection, timeout): {errors_encountered}")

if __name__ == "__main__":
    run_test_harness()
