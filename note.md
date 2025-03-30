## 💾 六、打包为 `.exe`（可选）

### 安装打包工具 PyInstaller：



```bash
pip install pyinstaller
```

### 打包指令：



```bash
pyinstaller --onefile --noconsole main.py
```



## 🔐 七、安全提示（重要）123456

- 主密码**不要忘记**，否则加密数据没法解密，数据就丢了。
- 数据保存在本地文件 `encrypted_data.dat`，是加密的，但如果主密码太简单，也可能被暴力破解。
- 你可以增强安全：加上密码强度检测、隐藏密码显示、支持导出/导入等。





https://ttkbootstrap.readthedocs.io/en/latest/themes/light/