import traceback

# TODO: weekly
VALID_TIME_FRAMES = ['1min', '2min', '3min', '5min', '15min', '30min', '60min'] # Must be valid pandas freq. values

def try_process_symbol(fun, symbol):
    try:
        fun(symbol)
    except Exception as e:
        print(f"Error processing symbol {symbol}: {e}. Skipping.")
        traceback.print_exc()
        return None


def weekday_to_string(weekday):
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return days[weekday]
