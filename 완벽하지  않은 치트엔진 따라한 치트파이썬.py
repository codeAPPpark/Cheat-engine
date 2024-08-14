import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar, Label, Entry, Button
import psutil
import pymem
import pymem.process

class MemoryEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cheat Engine Style Memory Editor")
        self.root.geometry("800x600")

        self.process_listbox = Listbox(root)
        self.process_listbox.pack(pady=10, fill=tk.BOTH, expand=True)

        scrollbar = Scrollbar(self.process_listbox)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.process_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.process_listbox.yview)

        self.update_process_list()

        self.select_process_button = Button(root, text="Select Process", command=self.select_process)
        self.select_process_button.pack(pady=10)

        self.address_label = Label(root, text="Memory Address (Hex):")
        self.address_label.pack()
        self.address_entry = Entry(root)
        self.address_entry.pack()

        self.value_label = Label(root, text="New 4-Bit Value (0-15):")
        self.value_label.pack()
        self.value_entry = Entry(root)
        self.value_entry.pack()

        self.search_value_label = Label(root, text="Search 4-Bit Value (0-15):")
        self.search_value_label.pack()
        self.search_value_entry = Entry(root)
        self.search_value_entry.pack()

        self.write_button = Button(root, text="Write 4-Bit Value", command=self.write_value)
        self.write_button.pack(pady=10)

        self.search_button = Button(root, text="Search 4-Bit Value", command=self.search_value)
        self.search_button.pack(pady=10)

        self.found_addresses = []

        self.pm = None
        self.selected_process_name = None
        self.selected_process_pid = None

    def update_process_list(self):
        self.process_listbox.delete(0, tk.END)
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] not in ("System Idle Process", "System") and proc.info['pid'] != 0:
                    self.process_listbox.insert(tk.END, f"{proc.info['name']} (PID: {proc.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def select_process(self):
        selected_process = self.process_listbox.get(tk.ACTIVE)
        if selected_process:
            process_name = selected_process.split(" (PID:")[0]
            pid = int(selected_process.split("PID: ")[1][:-1])
            try:
                self.pm = pymem.Pymem(process_name)
                self.selected_process_name = process_name
                self.selected_process_pid = pid
                messagebox.showinfo("Success", f"Process {self.selected_process_name} selected successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open process: {str(e)}")

    def search_value(self):
        if not self.pm:
            messagebox.showerror("Error", "Please select a process first.")
            return

        try:
            search_value = int(self.search_value_entry.get())
            if search_value < 0 or search_value > 15:
                raise ValueError("4-bit value must be between 0 and 15")

            if not self.found_addresses:
                process_base = self.pm.process_base.lpBaseOfDll
                process_size = self.pm.process_base.SizeOfImage

                for address in range(process_base, process_base + process_size, 1):
                    try:
                        value = self.pm.read_uchar(address) & 0x0F
                        if value == search_value:
                            self.found_addresses.append(address)
                    except:
                        pass

                if self.found_addresses:
                    messagebox.showinfo("Search Result", f"Found {len(self.found_addresses)} addresses with value {search_value}.")
                else:
                    messagebox.showinfo("Search Result", "No addresses found.")
            else:
                new_addresses = []
                for address in self.found_addresses:
                    try:
                        value = self.pm.read_uchar(address) & 0x0F
                        if value == search_value:
                            new_addresses.append(address)
                    except:
                        pass

                self.found_addresses = new_addresses
                if self.found_addresses:
                    messagebox.showinfo("Search Result", f"Filtered down to {len(self.found_addresses)} addresses.")
                else:
                    messagebox.showinfo("Search Result", "No matching addresses found.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to search value: {str(e)}")

    def write_value(self):
        if not self.pm:
            messagebox.showerror("Error", "Please select a process first.")
            return

        try:
            new_value = int(self.value_entry.get())
            if new_value < 0 or new_value > 15:
                raise ValueError("4-bit value must be between 0 and 15")

            updated_count = 0
            for address in self.found_addresses:
                try:
                    original_value = self.pm.read_uchar(address)
                    new_value_combined = (original_value & 0xF0) | (new_value & 0x0F)
                    self.pm.write_uchar(address, new_value_combined)
                    updated_count += 1
                except:
                    pass

            messagebox.showinfo("Update Result", f"Updated {updated_count} addresses with new value {new_value}.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to write value: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MemoryEditorApp(root)
    root.mainloop()
