import os
import signal
import psutil
import platform


def find_and_close_roblox():
    print("\n=== CERRANDO PROCESOS ROBLOX ===\n")
    roblox_processes = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if "roblox" in proc.info["name"].lower():
                roblox_processes.append(proc)
                print(f"Encontrado: {proc.info['name']} (PID: {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if not roblox_processes:
        print("No se encontraron procesos de Roblox ejecutándose.")
        return

    for proc in roblox_processes:
        pid = proc.info["pid"]
        name = proc.info["name"]
        print(f"\nIntentando cerrar {name} (PID: {pid})...")
        try:
            if platform.system() == "Windows":
                proc.terminate()
                proc.wait(timeout=5)
            else:
                os.kill(pid, signal.SIGKILL)
            print(f"{name} cerrado.")
        except psutil.NoSuchProcess:
            print(f"Proceso {pid} ya no existe.")
        except psutil.AccessDenied:
            print(f"Sin permisos para cerrar proceso {pid}.")
        except Exception as e:
            print(f"Error al cerrar el proceso: {e}")
