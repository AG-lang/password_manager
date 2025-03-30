import json
import os
import base64
import hashlib
import pyperclip
import secrets
import string
import sys
from cryptography.fernet import Fernet
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# 获取运行目录，方便便携化
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "encrypted_data.dat")

# 生成密钥
def generate_key(master_password):
    hash = hashlib.sha256(master_password.encode()).digest()
    return base64.urlsafe_b64encode(hash)

# 加密/解密
def encrypt_data(data, key):
    return Fernet(key).encrypt(data.encode())

def decrypt_data(data, key):
    return Fernet(key).decrypt(data).decode()

# 加载/保存数据
def load_data(key):
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "rb") as f:
            encrypted_data = f.read()
        return json.loads(decrypt_data(encrypted_data, key))
    except Exception:
        ttk.Messagebox.show_error("错误", "无法解密数据。主密码错误或文件损坏。")
        return []

def save_data(data, key):
    try:
        encrypted = encrypt_data(json.dumps(data), key)
        with open(DATA_FILE, "wb") as f:
            f.write(encrypted)
    except Exception as e:
        ttk.Messagebox.show_error("错误", f"保存数据出错: {str(e)}")

# 生成随机密码
def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(chars) for _ in range(length))

# 主类
class PasswordManager:
    def __init__(self, master):
        self.master = master
        self.master.title("密码管理器")
        self.master.geometry("900x500")
        self.master.resizable(True, True)

        self.key = None
        self.data = []
        self.show_passwords = False

        self.prompt_master_password()

    def prompt_master_password(self):
        popup = ttk.Toplevel(self.master)
        popup.title("请输入主密码")
        popup.geometry("300x150")
        popup.attributes("-topmost", True)
        popup.grab_set()
        popup.focus_force()

        ttk.Label(popup, text="主密码:").pack(pady=10)
        password_entry = ttk.Entry(popup, show="*")
        password_entry.pack(pady=5)
        password_entry.focus()

        def on_submit():
            password = password_entry.get()
            if not password:
                ttk.Messagebox.show_warning("提示", "请输入主密码")
                return
            self.key = generate_key(password)
            self.data = load_data(self.key)
            popup.destroy()
            self.build_ui()

        password_entry.bind("<Return>", lambda e: on_submit())
        ttk.Button(popup, text="确认", command=on_submit).pack(pady=10)

    def build_ui(self):
        # 搜索框
        search_frame = ttk.Frame(self.master)
        search_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(search_frame, text="搜索:").grid(row=0, column=0)
        self.search_var = ttk.StringVar()
        self.search_var.trace("w", lambda *args: self.refresh_table())
        ttk.Entry(search_frame, textvariable=self.search_var, width=40).grid(row=0, column=1, padx=5)

        # 表格
        columns = ("site", "username", "password", "note")
        self.tree = ttk.Treeview(self.master, columns=columns, show="headings", bootstyle="dark")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180 if col != "note" else 300)
        self.tree.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.tree.bind("<Double-1>", self.show_detail)

        # 按钮区
        btn_frame = ttk.Frame(self.master)
        btn_frame.grid(row=2, column=0, pady=10)

        ttk.Button(btn_frame, text="添加密码", command=self.open_add_window).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="修改", command=self.edit_password).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="删除", command=self.delete_password).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="复制密码", command=self.copy_password).grid(row=0, column=3, padx=5)

        self.toggle_btn = ttk.Button(btn_frame, text="显示密码", command=self.toggle_password_visibility)
        self.toggle_btn.grid(row=0, column=4, padx=5)

        # 响应式布局权重
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        self.master.lift()
        self.master.attributes("-topmost", True)
        self.master.focus_force()
        self.master.after(500, lambda: self.master.attributes("-topmost", False))

        self.refresh_table()

    def refresh_table(self):
        keyword = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
        for i in self.tree.get_children():
            self.tree.delete(i)
        for entry in self.data:
            if keyword:
                if keyword not in entry["site"].lower() and \
                   keyword not in entry["username"].lower() and \
                   keyword not in entry.get("note", "").lower():
                    continue
            pwd = entry['password'] if self.show_passwords else '*' * len(entry['password'])
            note = entry.get("note", "")
            self.tree.insert("", "end", values=(entry["site"], entry["username"], pwd, note))

    def open_add_window(self):
        win = ttk.Toplevel(self.master)
        win.title("添加密码")
        win.geometry("400x300")
        win.grab_set()

        labels = ["网站", "用户名", "密码", "备注"]
        vars = [ttk.StringVar() for _ in range(4)]

        for i, label in enumerate(labels):
            ttk.Label(win, text=label + ":").grid(row=i, column=0, sticky="e", padx=5, pady=5)
            ttk.Entry(win, textvariable=vars[i], width=30).grid(row=i, column=1, padx=5, pady=5)

        def fill_random():
            vars[2].set(generate_random_password())

        ttk.Button(win, text="生成随机密码", command=fill_random).grid(row=2, column=2, padx=5)

        def save():
            values = [v.get() for v in vars]
            if not all(values[:3]):
                ttk.Messagebox.show_warning("提示", "请填写完整信息")
                return
            self.data.append({
                "site": values[0],
                "username": values[1],
                "password": values[2],
                "note": values[3]
            })
            save_data(self.data, self.key)
            self.refresh_table()
            win.destroy()
            ttk.Messagebox.show_info("成功", "密码已保存！")

        ttk.Button(win, text="保存", command=save).grid(row=5, column=1, pady=10)

    def delete_password(self):
        selected = self.tree.selection()
        if not selected:
            ttk.Messagebox.show_warning("提示", "请先选择一条记录")
            return
        index = self.tree.index(selected[0])
        confirm = ttk.Messagebox.askyesno("确认", "确定删除这条记录？")
        if confirm:
            del self.data[index]
            save_data(self.data, self.key)
            self.refresh_table()

    def edit_password(self):
        selected = self.tree.selection()
        if not selected:
            ttk.Messagebox.show_warning("提示", "请先选择一条记录")
            return
        index = self.tree.index(selected[0])
        entry = self.data[index]

        win = ttk.Toplevel(self.master)
        win.title("修改密码")
        win.geometry("400x300")
        win.grab_set()

        fields = ["网站", "用户名", "密码", "备注"]
        keys = ["site", "username", "password", "note"]
        vars = [ttk.StringVar(value=entry.get(k, "")) for k in keys]

        for i, label in enumerate(fields):
            ttk.Label(win, text=label + ":").grid(row=i, column=0, sticky="e", padx=5, pady=5)
            ttk.Entry(win, textvariable=vars[i], width=30).grid(row=i, column=1, padx=5, pady=5)

        def save_edit():
            for i, k in enumerate(keys):
                entry[k] = vars[i].get()
            save_data(self.data, self.key)
            self.refresh_table()
            win.destroy()
            ttk.Messagebox.show_info("成功", "修改完成！")

        ttk.Button(win, text="保存修改", command=save_edit).grid(row=5, column=1, pady=10)

    def copy_password(self):
        selected = self.tree.selection()
        if not selected:
            ttk.Messagebox.show_warning("提示", "请先选择一条记录")
            return
        index = self.tree.index(selected[0])
        password = self.data[index]['password']
        pyperclip.copy(password)
        ttk.Messagebox.show_info("已复制", "密码已复制到剪贴板！")

    def toggle_password_visibility(self):
        self.show_passwords = not self.show_passwords
        self.toggle_btn.config(text="隐藏密码" if self.show_passwords else "显示密码")
        self.refresh_table()

    def show_detail(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        index = self.tree.index(selected[0])
        entry = self.data[index]

        win = ttk.Toplevel(self.master)
        win.title("详细信息")
        win.geometry("400x300")
        win.grab_set()

        for i, (k, v) in enumerate(entry.items()):
            ttk.Label(win, text=f"{k.capitalize()}:").grid(row=i, column=0, sticky="e", padx=5, pady=5)
            entry_box = ttk.Entry(win, width=40)
            entry_box.insert(0, v)
            entry_box.config(state="readonly")
            entry_box.grid(row=i, column=1, padx=5, pady=5)

        def copy_pwd():
            pyperclip.copy(entry["password"])
            ttk.Messagebox.show_info("成功", "密码已复制！")

        ttk.Button(win, text="复制密码", command=copy_pwd).grid(row=i + 1, column=1, pady=10)

# 启动
if __name__ == "__main__":
    app = ttk.Window(themename="solar")
    PasswordManager(app)
    app.mainloop()