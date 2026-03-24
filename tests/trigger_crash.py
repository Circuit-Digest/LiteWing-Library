"""
Example: Coredump Test Tool
===========================
This script allows you to intentionally trigger a system crash on the drone
to verify that the Coredump feature is working and capturing data to flash.

WARNING: This will make the drone reboot immediately! 
Do NOT run this while the drone is flying.

Crash Types:
1. Software Abort: Cleanest software crash.
2. Null Pointer: Simulates a common CPU exception (Guru Meditation).
3. Watchdog: Simulates a system freeze/lock-up.

# GDB Debugging Commands Reference (Useful when diagnosing drone firmware crashes)
# IDF Terminal: python $env:IDF_PATH/components/espcoredump/espcoredump.py -p COM9 dbg_corefile build/ESPDrone.elf
# IDF Terminal: python $env:IDF_PATH/components/partition_table/parttool.py -p COM9 erase_partition --partition-type=data --partition-subtype=coredump
# Command        Purpose                                                   Why it helps your Drone
# ---------------------------------------------------------------------------------------------------------------
# bt             Backtrace: Shows the chain of function calls leading      Finds the exact line of code that
#                to the crash.                                             failed (e.g., in the PID loop).
#
# bt full        Detailed Backtrace: Shows the backtrace plus all local    Lets you see sensor values,
#                variables for every function.                             coordinates, or state variables
#                                                                          at every step of the failure.
#
# info threads   Task List: Lists all FreeRTOS tasks and their current     Helps identify if a task like
#                state.                                                    "Stabilizer" or "Radio" was stuck
#                                                                          or blocked when the crash occurred.
#
# frame <#>      Switch Context: Moves the debugger to a specific level    If `bt` shows frame #3 is your
#                in the backtrace.                                         code, run `frame 3` to inspect
#                                                                          variables in that stack frame.
#
# p <var>        Print: Displays the value of a specific variable.         Useful to verify values such as
#                                                                          `p target_pitch` to see if the
#                                                                          control system produced an
#                                                                          impossible value.
#
# info locals    Local Variables: Lists all variables in the current       Quickly inspect all intermediate
#                function.                                                 calculations inside the current
#                                                                          function.
#
# info args      Arguments: Shows values passed into the current           Helps detect bad inputs such as
#                function.                                                 NULL pointers or unexpected zeros.
#
# list           Source View: Shows ~10 lines of source code around        Gives context for the logic near
#                the current crash point.                                  the failure without opening the IDE.
#
# info registers CPU State: Displays raw processor register values.       Useful for diagnosing low-level
#                                                                          faults like Divide-by-Zero or
#                                                                          Stack Overflow.
#
# q              Quit: Exits the GDB session.                              Safely closes the debugger and
#                                                                          returns to the terminal.

"""

from litewing import LiteWing
import time

def main():
    # 1. Initialize drone (connect via WiFi)
    drone = LiteWing()
    
    try:
        drone.connect()
        
        print("\n--- LiteWing Coredump Test Tool ---")
        print("1. Soft Abort (abort)")
        print("2. Null Pointer Dereference (Guru Meditation)")
        print("3. Task Lockup (Watchdog Timeout)")
        print("q. Quit")
        
        choice = input("\nSelect crash type to trigger: ").strip().lower()
        
        if choice == 'q':
            return

        if choice not in ['1', '2', '3']:
            print("Invalid selection.")
            return

        crash_type = int(choice)
        
        print(f"\nTriggering crash type {crash_type}...")
        print("Drone will reboot in 3... 2... 1...")
        time.sleep(1)

        # 2. Access the low-level Crazyflie instance
        # We use Port 0x08 (SETPOINT_HL) and Command 0xFE (our custom crash cmd)
        cf = drone._cf_instance
        
        # Construct the payload: [CommandID, CrashType]
        payload = bytes([0xFE, crash_type])
        
        # Send raw CRTP packet using internal library helper
        # Port 8 = High Level Commander, Channel 0
        from litewing._crtp import send_crtp_with_fallback
        send_crtp_with_fallback(cf, port=0x08, channel=0, payload=payload)
        
        print("\nCommand sent! Check your serial console for Panic/Coredump logs.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        drone.disconnect()

if __name__ == "__main__":
    main()
