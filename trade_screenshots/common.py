import traceback


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
