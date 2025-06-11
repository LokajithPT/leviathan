import win32serviceutil
import win32service
import win32event
import win32api
import servicemanager
import os
import sys

class WakeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "WakeDaemon"
    _svc_display_name_ = "Wake Voice Listener Service"
    _svc_description_ = "Runs the wake.exe voice listener in background."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.exe_path = os.path.join(os.getenv("ProgramFiles"), "WakeDaemon", "wake.exe")

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("WakeDaemon service starting...")
        os.system(f'"{self.exe_path}"')
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        win32serviceutil.HandleCommandLine(WakeService)
    else:
        win32serviceutil.HandleCommandLine(WakeService)

