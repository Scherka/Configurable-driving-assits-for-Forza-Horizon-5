from multiprocessing import Process, freeze_support
from main_window import start_main_window

if __name__ == "__main__":
    freeze_support()
    try:
        main_window_process = Process(target=start_main_window)
        main_window_process.start()
        main_window_process.join()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if main_window_process and main_window_process.is_alive():
            main_window_process.terminate()
            main_window_process.join()