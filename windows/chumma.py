import win32serviceutil
import win32service
import win32event
import win32api
import win32con
import servicemanager
import os
import sys

class WakeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "WakeListener"
    _svc_display_name_ = "Wake Voice Listener Service"
    _svc_description_ = "Listens for wake word and triggers actions silently."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.exe_path = r"C:\Path\To\wake.exe"  # CHANGE THIS TO YOUR ACTUAL PATH

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("Starting WakeListener Service...")
        # Launch wake.exe as a detached background process
        try:
            win32api.ShellExecute(
                0,
                "open",
                self.exe_path,
                None,
                os.path.dirname(self.exe_path),
                win32con.SW_HIDE
            )
        except Exception as e:
            servicemanager.LogErrorMsg(f"Error running wake.exe: {e}")

        # Wait until service is stopped
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Run as a service
        win32serviceutil.HandleCommandLine(WakeService)
    else:
        win32serviceutil.HandleCommandLine(WakeService)

