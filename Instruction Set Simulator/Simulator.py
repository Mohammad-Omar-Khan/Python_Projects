import tkinter as tk
from tkinter import *
from tkinter import filedialog
import numpy as np
from tkinter import ttk 
import time


class RAM:
    def __init__(self, size):
        self.size = size
        self.memory = [0] * size

    def read(self, address):
        if address < self.size:
            # print(self.memory[address],"RAM")
            return self.memory[address]
        else:
            raise ValueError("Invalid memory address: {}".format(address))

    def write(self, address, value):
        if address < self.size:
            self.memory[address] = value
            print(self.memory)
        else:
            raise ValueError("Invalid memory address: {}".format(address))


class CPU:
    def __init__(self, ram):
        self.ram = ram
        self.registers = {
            0: 0,  # 2 accumulators (A:0, B:1)
            1: 0,
            "E": 0,
            "PC": 0,
            "IR": 0,
            "AR": 0,
            "DR": 0,
            "TR": 0,
            "XR": 0,
            "B": 0,
            "C": 0,
            "F": 0,
            "INPR": 0,
            "OUTR": 0,
            "CMP_FLAG_B": 0,
            "CMP_FLAG_C": 0,
            "CMP_FLAG_D": 0,
            "INP_FLAG": 0,
            "OUT_FLAG": 0,
            "IEN": 0
            # 'FLAGS': 0, # will need to add more flags, with their specific names, as required
        }
        self.S_flip_flop = 0
        self.__clock_speed = 1

    def set_clock_speed(self, cycles_per_second):
        self.__clock_speed = cycles_per_second

    def get_speed(self) -> int:
        return int((1 / self.__clock_speed) * 1000)

    def fetch(self):
        pc = self.registers["PC"]
        instruction = self.ram.read(pc)
        self.registers['AR'] = instruction
        self.registers["PC"] += 1
        self.registers["IR"] = instruction
        return instruction

    def decode(self, instruction):
        a = (instruction >> 14) & 0b11  # addressing mode (direct or indirect)
        op_code = (instruction >> 10) & 0b1111  # operation code (opcode)
        d = (instruction >> 9) & 0b1  # accumulator selector
        s = (instruction >> 8) & 0b1  # register selector
        m = instruction & 0b11111111  # memory address/location
        # x = (instruction >> 4) & 0b1111
        # y = instruction & 0b1111
        # j = instruction & 0b11111111
        print(bin(a), bin(op_code), bin(d), bin(s), bin(m))
        return op_code, a, d, s, m

    def execute(self, op_code, a, d, s, m):
        # print('instruction:', op_code, a, d, s, m, x, y, j)
        # memory reference instructions
        # print(d, "this is d")
        
        if op_code == 0b0000:  # LD
            if a == 0:
                self.registers['DR'] = self.ram.read(m)
                self.registers[d] = self.registers['DR']
            elif a == 1:
                self.registers['DR'] = self.ram.read(self.ram.read(m))
                self.registers[d] = self.registers['DR']
            elif a == 2:
                self.registers['DR'] = m
                self.registers[d] = self.registers['DR']
            elif a == 3:
                m = m + self.registers['XR']
                self.registers['DR'] = self.ram.read(m)
                self.registers[d] = self.registers['DR']
        elif op_code == 0b0001:  # STR
            self.ram.write(m, self.registers[d])
        elif op_code == 0b0010:  # ADD
            self.registers['DR'] = self.ram.read(m)
            self.registers[d] = self.registers[s] + self.registers['DR']
        elif op_code == 0b0011:  # SUB
            self.registers['DR'] = self.ram.read(m)
            self.registers[d] = self.registers[s] - self.registers['DR']
        elif op_code == 0b0100:  # MUL
            self.registers['DR'] = self.ram.read(m)
            self.registers[d] = self.registers[s] * self.registers['DR']
        elif op_code == 0b0101:  # DIV
            self.registers['DR'] = self.ram.read(m)
            self.registers[d] = self.registers[s] // self.registers['DR']
        elif op_code == 0b0110:  # AND
            self.registers['DR'] = self.ram.read(m)
            self.registers[d] = self.registers[s] & self.registers['DR']
        elif op_code == 0b0111:  # OR
            self.registers['DR'] = self.ram.read(m)
            self.registers[d] = self.registers[s] | self.registers['DR']
        elif op_code == 0b1000:  # XOR
            self.registers['DR'] = self.ram.read(m)
            self.registers[d] = self.registers[s] ^ self.registers['DR']
        elif op_code == 0b1001:  # JMP
            self.ram.write(m, self.registers["PC"])
            m += 1
            self.registers["PC"] = m
        elif op_code == 0b1010:  # JEQ
            self.registers['B'] = 1 if self.registers[s] == self.registers[d] else 0
            if self.registers['B'] and a:
                self.registers["PC"] = self.ram.read(m)
            elif self.registers['B']:
                self.registers['PC'] = m
        elif op_code == 0b1011:  # JNE
            self.registers['B'] = 0 if self.registers[s] != self.registers[d] else 1
            if ~self.registers['B'] and a:
                self.registers["PC"] = self.ram.read(m)
            elif ~self.registers['B']:
                self.registers['PC'] = m
        elif op_code == 0b1100:  # JGT
            self.registers['C'] = 1 if self.registers[s] < self.registers[d] else 0
            if self.registers['C'] and a:
                self.registers["PC"] = self.ram.read(m)
            elif self.registers['C']:
                self.registers['PC'] = m
        elif op_code == 0b1101:  # JLT
            self.registers['F'] = 1 if self.registers[s] > self.registers[d] else 0
            if self.registers['F'] and a:
                self.registers["PC"] = self.ram.read(m)
            elif self.registers['F']:
                self.registers['PC'] = m
        elif op_code == 0b1110:  #STX
            self.registers['XR'] = self.registers[d] # *************FIX*************
        # register reference instructions
        elif op_code == 0b1111 and m == 1:  # MOV
            self.registers['TR'] = self.registers[s]
            self.registers[d] = self.registers['TR']
        elif op_code == 0b1111 and m == 2:  # INC
            self.registers[d] += 1
        elif op_code == 0b1111 and m == 4:  # DEC
            self.registers[d] -= 1
        elif op_code == 0b1111 and m == 8:  # CMP
            if self.registers[d] == self.registers[s]:
                self.registers["CMP_FLAG"] = 1
        elif op_code == 0b1111 and m == 16:  # NOT
            self.registers[d] = ~self.registers[d]
        elif op_code == 0b1111 and m == 32:  # SHL
            self.registers[d] = self.registers[d] << 1
        elif op_code == 0b1111 and m == 64:  # SHR
            self.registers[d] = self.registers[d] >> 1
        elif op_code == 0b1111 and m == 128:  # CLA
            self.registers[d] = 0
        elif op_code == 0b1111 and m == 129:  # CLE
            self.registers["E"] = 0
        elif op_code == 0b1111 and m == 130:  # CLB
            self.registers["B"] = 0
        elif op_code == 0b1111 and m == 132:  # CLC
            self.registers["C"] = 0
        elif op_code == 0b1111 and m == 136:  # CLF
            self.registers["F"] = 0
        elif op_code == 0b1111 and m == 144:  # SPA
            value = self.registers[d]
            signed_bit = (value >> 15) & 0b1
            if ~signed_bit:
                self.registers["PC"] += 1
        elif op_code == 0b1111 and m == 160:  # SNA
            value = self.registers[d]
            signed_bit = (value >> 15) & 0b1
            if signed_bit:
                self.registers["PC"] += 1
        elif op_code == 0b1111 and m == 192:  # SZA
            value = self.registers[d]
            if value == 0:
                self.registers["PC"] += 1
        elif op_code == 0b1111 and m == 193:  # HLT
            print("HLT")
            self.S_flip_flop = 0
        # input/output reference instructions
        elif a == 1 and op_code == 0b1111 and m == 1:  # INP
            self.registers[d] = self.registers["INPR"]
            self.registers["INP_FLAG"] = 0
        elif a == 1 and op_code == 0b1111 and m == 2:  # OUT
            self.registers["OUTR"] = self.registers[d]
            self.registers["OUT_FLAG"] = 0
        elif a == 1 and op_code == 0b1111 and m == 4:  # SKI
            if self.registers["INP_FLAG"] == 1:
                self.registers["PC"] += 1
        elif a == 1 and op_code == 0b1111 and m == 8:  # SKO
            if self.registers["OUT_FLAG"] == 1:
                self.registers["PC"] += 1
        elif a == 1 and op_code == 0b1111 and m == 16:  # ION
            self.registers["IEN"] == 1
        elif a == 1 and op_code == 0b1111 and m == 32:  # IOF
            self.registers["IEN"] == 0
        else:
            print(f"Unknown opcode: {op_code}")

        # print('A: ', self.registers[0], ', B: ', self.registers[1], ', Opcode: ', op_code)
        # print(self.ram.read(8), op_code)

        # self.program_counter += 1

    # def run(self):
    #     while True:
    #         instruction = self.fetch()
    #         op_code, a, d, s, m = cpu.decode(instruction)
    #         cpu.execute(op_code, a, d, s, m)
    #         time.sleep(1 / self.__clock_speed)


class RAM_UI(tk.Frame):
    def __init__(self, master, cpu):
        super().__init__(master)
        self.ram = cpu.ram

        self.memory_frame = tk.Frame(self)
        self.memory_frame.pack(padx = 100)

        self.memory_labels = []
        for i in range(cpu.ram.size):
            label = tk.Label(self.memory_frame,
                text="{}: {}".format(i, format(cpu.ram.read(i), "016b")),)
            label.grid(row=i//2, column=i%2, padx=10, pady=5)
            self.memory_labels.append(label)

    def update(self):
        for i in range(self.ram.size):
            self.memory_labels[i].config(
                text="{}: {}".format(i, format(self.ram.read(i), "016b"))
            )


class Registers_UI(tk.Frame):
    def __init__(self, master, cpu):
        super().__init__(master)
        self.registers = cpu.registers

        self.register_frame = tk.Frame(self)
        self.register_frame.pack(padx=100)

        self.register_labels = {}
        for i, reg_name in enumerate(self.registers):
            reg_label = tk.Label(self.register_frame, text=reg_name)
            reg_label.grid(row=i, column=0)

            value_label = tk.Label(
                self.register_frame, text="{0:04X}".format(self.registers[reg_name])
            )
            value_label.grid(row=i, column=1)

            self.register_labels[reg_name] = value_label

    def update(self):
        for key, value in self.register_labels.items():
            if key in self.registers:
                value.config(text="{0:04X}".format(self.registers[key]))
            else:
                value.config(text="----")


class Program_Input_UI(tk.Frame):
    def __init__(self, master, cpu):
        super().__init__(master)

        self.input_frame = tk.Frame(self)
        self.input_frame.pack()

        self.filename = None
        self.prg = None
        self.mr_opcodes = {
            "LD": "0000",
            "STR": "0001",
            "ADD": "0010",
            "SUB": "0011",
            "MUL": "0100",
            "DIV": "0101",
            "AND": "0110",
            "OR": "0111",
            "XOR": "1000",
            "JMP": "1001",
            "JEQ": "1010",
            "JNE": "1011",
            "JGT": "1100",
            "JLT": "1101",
            "STX": "1110",
        }
        self.rr_opcodes = {
            "MOV": "00000001",
            "INC": "00000010",
            "DEC": "00000100",
            "CMP": "00001000",
            "NOT": "00010000",
            "SHL": "00100000",
            "SHR": "01000000",
            "CLA": "10000000",
            "CLE": "10000001",
            "CLB": "10000010",
            "CLC": "10000100",
            "CLF": "10001000",
            "SPA": "10010000",
            "SNA": "10100000",
            "SZA": "11000000",
            "HLT": "11000001",
        }
        self.ior_opcodes = {
            "INP": "00000001",
            "OUT": "00000010",
            "SKI": "00000100",
            "SKO": "00001000",
            "ION": "00010000",
            "IOF": "00100000",
        }
        self.reg_selectors = {
            "AC0": "0",
            "AC1": "1",
        }

        style = ttk.Style()

        style.configure('RoundedButton.TButton', borderwidth=2, relief='ridge', background='#4caf50', foreground='black',
                padding=(10,5), font=('Arial', 12))
        button1 = ttk.Button(
            self.input_frame,
            text="Upload Program",
            style='RoundedButton.TButton',
            command=self.browse_files,
        )

        button1.grid(row=0, column=0, padx = 10, pady= 10)

        textLabel = Label(
            self.input_frame, text="Write a program in the textbox below: ", pady=5
        )
        textLabel.grid(row=2, column=0, columnspan=2)

        self.textBox = Text(self.input_frame, height=10, width=50, border=2)
        self.textBox.grid(row=3, column=0, columnspan=2)
        



        buttonCommit = ttk.Button(
            self.input_frame,
            style='RoundedButton.TButton',
            text="Load Program through input from textbox",
            command=self.retrieve_input,
        )
        buttonCommit.grid(row=0, column=1,padx = 10, pady= 10)

        button2 = ttk.Button(
            self.input_frame,
            text="Load Program through uploaded file",
            style='RoundedButton.TButton',
            command=self.read_program,
        )
        button2.grid(row=1, column=1,padx = 5, pady= 10)

        button3 = ttk.Button(
            self.input_frame,
            text="Run Program",
            style='RoundedButton.TButton',
            command=lambda: load_program(cpu, self.prg),
        )
        button3.grid(row=1, column=0,padx = 5, pady= 10)
        
    def browse_files(self):
        # use instance variable self.filename
        self.filename = filedialog.askopenfilename(
            initialdir="./",
            title="Select a File",
            filetypes=(("Text files", "*.txt*"), ("All Files", "*.*")),
        )

    def read_program(self):
        text_file = open(self.filename, "r")
        lines = text_file.read().split("\n")
        self.prg = []

        for line in lines:
            self.prg.append(int(self.decipher(line), 2))
            print(format(int(self.decipher(line), 2), "#018b"))
        print(self.prg)

    def retrieve_input(self):
        global inputValue
        inputValue = self.textBox.get("1.0", "end-1c")
        lines = inputValue.split("\n")
        self.prg = []

        for line in lines:
            instruction = self.decipher(line)
            self.prg.append(int(self.decipher(line), 2))
            # print(instruction)
            # print(format(int(self.decipher(line), 2), "#018b"))
        print(self.prg)

    def decipher(self, line):
        instruction = ""
        line_queue = line.split(" ")
        exception = FALSE
        reg = ''
        print(line)

        while len(line_queue) > 0:
            ins = line_queue.pop(0)
            print(ins, instruction)

            if ins == "HLT":
                instruction = "0011110011000001"
            elif ins == "CLA":
                instruction = "0011110010000000"
            elif ins == "CLE":
                instruction = "0011110010000001"
            elif ins == "CLB":
                instruction = "0011110010000010"
            elif ins == "CLC":
                instruction = "0011110010000100"
            elif ins == "CLF":
                instruction = "0011110010001000"
            
            if (ins in {"HLT", "CLA", "CLE", "CLB", "CLC", "CLF"}): return instruction
            
            if ins == "I" and ins == line[0]:
                instruction += '01'
            elif ins == '$' and ins == line[0]:
                instruction += '10'
            elif ins == '!' and ins == line[0]:
                instruction += '11'
            elif ins == line.split(" ")[0]:
                instruction += '00'

            if ins in self.mr_opcodes:
                instruction += self.mr_opcodes[ins]

                if ins in {"LD", "STR", "JMP"}:
                    if ins == "JMP": instruction += '00'
                    exception = True
            elif ins in self.rr_opcodes:
                instruction += "1111"
                reg += self.rr_opcodes[ins]

                if ins not in {"MOV", "CMP"}:
                    exception = True

            if ins in self.reg_selectors:
                instruction += self.reg_selectors[ins]

                if (exception):
                    instruction += '0'
            
            if ins.isdigit():
                instruction += format(int(ins), '08b')

        if reg:
            instruction += reg

        return instruction
        # print(instruction)

    # def update(self):

class Application(tk.Frame):
    def __init__(self, cpu, master=None):
        super().__init__(master)
        self.master = master
        self.cpu = cpu
        self.input_ui = Program_Input_UI(self, cpu)
        self.input_ui.pack()
        self.ram_ui = RAM_UI(self, cpu)
        self.ram_ui.pack(side=tk.RIGHT)
        self.register_ui = Registers_UI(self, cpu)
        self.register_ui.pack(side=tk.LEFT)
        self.pack()

    def update(self):
        # print('mem location:', self.cpu.registers['PC'])
        self.ram_ui.update()
        self.register_ui.update()
        instruction = self.cpu.fetch()
        op_code, a, d, s, m = self.cpu.decode(instruction)
        self.cpu.execute(op_code, a, d, s, m)
        print(cpu.S_flip_flop, "s flip flop in application update")
        if self.cpu.S_flip_flop:
            print("hello!!!")
            self.after(self.cpu.get_speed(), self.update)
        # else:
        #     self.cpu.ram = RAM(30)
        #     self.cpu.registers = {
        #         0: 0,  # 2 accumulators (A:0, B:1)
        #         1: 0,
        #         "E": 0,
        #         "PC": 0,
        #         "IR": 0,
        #         "AR": 0,
        #         "DR": 0,
        #         "TR": 0,
        #         "INPR": 0,
        #         "OUTR": 0,
        #         "CMP_FLAG_B": 0,
        #         "CMP_FLAG_C": 0,
        #         "CMP_FLAG_D": 0,
        #         "INP_FLAG": 0,
        #         "OUT_FLAG": 0,
        #         "IEN": 0
        #     }
        #     self.ram_ui.destroy()
        #     self.register_ui.destroy()
        #     self.cpu.S_flip_flop = 1
        #     self.ram_ui = RAM_UI(self, cpu)
        #     self.ram_ui.pack(side=tk.RIGHT)
        #     self.register_ui = Registers_UI(self, cpu)
        #     self.register_ui.pack(side=tk.LEFT)
        #     self.pack()
        #     self.ram_ui.update()
        #     self.register_ui.update()


def load_program(cpu, program):
    # print("hello!!")
    cpu.S_flip_flop = 1
    for i, instruction in enumerate(program):
        print(i, instruction)
        cpu.ram.write(i, instruction)
        # print(cpu.S_flip_flop,"flip flop")

    app.update()

if __name__ == "__main__":
    ram = RAM(30)
    cpu = CPU(ram)
    # program = [
        # 0b0000000000001010,  # LD AC0 10
    #     0b0000010000001011,  # LD AC1 11
    #     0b0111100000000001,  # INC AC0
    #     0b0000100000010100,  # STR AC0 20
    #     0b0110110000000010,  # JGT AC1 AC0 2
    #     0b0000000000010100,  # LD AC0 20
    #     0b0111100000001000,  # NOT AC0
    #     0b0000100000010100,  # STR AC0 20
    #     0b0001000100000000,  # MOV AC0 AC1
    #     0b0111100010100000,  # HLT
    # ]
    # ADD AC0 DR
    cpu.ram.write(10, 12)
    cpu.ram.write(11, 6)
    cpu.ram.write(12, 1)
    # load_program(cpu, program)

    root = tk.Tk()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.geometry(f"{width}x{height}")
    app = Application(cpu, master=root)
    # app.input_ui.decipher("! LD AC1 10")
    # app.input_ui.decipher("STR AC1 10")
    # app.input_ui.decipher("ADD AC0 AC1 11")
    # app.input_ui.decipher("JMP 4")
    # app.input_ui.decipher("I JEQ AC0 AC1 4")
    # app.input_ui.decipher("JGT AC1 AC0 4")
    # app.input_ui.decipher("MOV AC1 AC0")
    # app.input_ui.decipher("INC AC1")
    # app.input_ui.decipher("DEC AC0")
    # app.input_ui.decipher("NOT AC1")
    # app.input_ui.decipher("SHL AC1")
    # app.input_ui.decipher("SPA AC1")
    # app.input_ui.decipher("HLT")
    # app.input_ui.decipher("CLE")

    root.title("Computer Organization and Assembly Language Project - Simulator")
    # app.cpu.decode(0b1001100110001010)
    # app.update()
    app.mainloop()

# LD AC0 10
# LD AC1 11
# INC AC0
# STR AC0 20
# JGT AC1 AC0 2
# LD AC0 20
# NOT AC0
# STR AC0 20
# MOV AC0 AC1
# HLT

# LD AC0 10
# JMP 4
# INC AC0
# HLT
# INC AC0
# ADD AC0 AC0 11
# MOV AC1 AC0
# I JEQ AC0 AC1 4
