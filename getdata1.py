import re, sys, os
import subprocess
import json


class GetData:

    def split_lines(self, s):
        """Splits lines in a way that works even on Windows and old devices.
        Windows will see \r\n instead of \n, old devices do the same, old devices
        on Windows will see \r\r\n.
        """
        # rstrip is used here to workaround a difference between splineslines and
        # re.split:
        # >>> 'foo\n'.splitlines()
        # ['foo']
        # >>> re.split(r'\n', 'foo\n')
        # ['foo', '']
        return re.split(r'[\r\n]+', s.rstrip())

    def get_devices(self, adb_path='adb'):
        with open(os.devnull, 'wb') as devnull:
            subprocess.check_call([adb_path, 'start-server'], stdout=devnull,
                                  stderr=devnull)
        out = self.split_lines(
            subprocess.check_output([adb_path, 'devices']).decode('utf-8'))
        # The first line of `adb devices` just says "List of attached devices", so
        # skip that.
        devices = []
        for line in out[1:]:
            if not line.strip():
                continue
            if 'offline' in line:
                continue
            serial, _ = re.split(r'\s+', line, maxsplit=1)
            devices.append(serial)
        return devices

    def getmeminfo(self, pname):
        line_dict = {}
        ls = subprocess.Popen(["adb", "shell", "dumpsys", "meminfo", pname, " | grep -E", "'Native Heap|TOTAL'"],
                              stdout=subprocess.PIPE)
        out = ls.stdout.readlines()
        for line in out:
            if re.search("Native Heap", line):
                line = line.strip("\n")
                line_array = line.split(" ")
                line_array = " ".join(line_array).split()
                line_dict["Native_Pss"] = int(line_array[2])
                line_dict["Native_Heap_Alloc"] = int(line_array[-2])
                line_dict["Native_Heap_Free"] = int(line_array[-1])

                for line_sub in out:
                    if re.search("TOTAL", line_sub):
                        line_sub = line_sub.strip("\n")
                        line_array = line_sub.split(" ")
                        line_array = " ".join(line_array).split()
                        line_dict["Total_Pss"] = int(line_array[1])
                        line_dict["Total_Heap_Alloc"] = int(line_array[-2])
                        line_dict["Total_Heap_Free"] = int(line_array[-1])
                        break
            break

        if line_dict:
            return json.dumps(line_dict)
        return "App not started.Unable to fetch meminfo...."

    def getcpuinfo(self, pname):
        lm = subprocess.Popen(["adb", "shell", "dumpsys", "cpuinfo", "| grep -i", pname], stdout=subprocess.PIPE)
        out = lm.stdout.readlines()
        for line in out:
            return line.strip("\n")
        else:
            return "App not started.Unable to fetch cpuinfo"

    def getcpucores(self):
        line_dict_cpu = {}
        try:
            for i in range(1, 5):
                lo = subprocess.Popen(["adb shell cat sys / devices / system / cpu / cpu" + str(i) +
                                       " / cpufreq / scaling_cur_freq"],
                                      stdout=subprocess.PIPE)
                out = lo.stdout.readlines()
                line_dict_cpu["CPU" + str(i)] = out
        except OSError:
            return "Unable to fetch CPU core details"

        if line_dict_cpu:
            return line_dict_cpu
        return "App not started.Unable to fetch CPU Core"

    def getJenkyFrames(self):
        jenky_frames_output = os.popen("adb shell dumpsys gfxinfo")
        for count, line in enumerate(jenky_frames_output.readlines()):
            if 'Janky frame' in line:
                return str(line.split()[-2])

    def getbatterystats(self):
        try:
            out = os.popen("adb shell dumpsys batterystats")
            return out.readlines()[0]
        except OSError:
            return "Unable to fetch Battery Stats"

    def getcurrentevent(self):
        try:
            out = os.popen("adb logcat -d| grep cmp | tail -1")
            s = out.readlines()[0]
            return s[s.find("{")+1:s.find("}")]

        except OSError:
            return "Unable to fetch current event"
