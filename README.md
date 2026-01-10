# 豆包深度研究自动化脚本

这是一个使用 Python Selenium 实现的自动化脚本，用于访问豆包网站并执行深度研究功能。

## 功能特性

- 🌐 自动打开豆包网站
- 🔐 登录状态检测与引导
- 🎯 自动点击"深入研究"功能
- 📝 自动输入研究主题
- 📤 自动发送研究请求
- ⏳ 等待研究结果生成
- 📁 使用指定目录存储浏览器数据（位于 `D:\code\deep_research_fuse\workspace`）

## 目录结构

```
D:\code\deep_research_fuse\
├── doubao_research_auto.py     # 增强版本（主要使用）
├── config.py                  # 配置文件
├── run.py                     # 简易启动器
├── requirements.txt           # 依赖包列表
├── README.md                  # 说明文档
└── workspace/                 # 工作区目录
    ├── chrome_profile/         # Chrome用户数据目录
    ├── downloads/              # 下载目录
    └── logs/                   # 日志目录
```

## 环境要求

- Python 3.7+
- Chrome 浏览器
- ChromeDriver（与 Chrome 浏览器版本匹配）

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 ChromeDriver

#### 方法一：使用 webdriver-manager（推荐）

```bash
pip install webdriver-manager
```

然后修改脚本中的初始化部分：

```python
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 替换原来的 webdriver.Chrome()
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)
```

#### 方法二：手动下载

1. 查看您的 Chrome 浏览器版本（地址栏输入 `chrome://version`）
2. 下载对应版本的 ChromeDriver：https://chromedriver.chromium.org/downloads
3. 将 chromedriver.exe 放在系统 PATH 中或脚本同目录下

## 使用方法

### 运行脚本

```bash
python run.py
```

### 工作区配置

脚本已配置使用 `D:\code\deep_research_fuse\workspace` 作为工作目录：

- **Chrome 用户数据**：`workspace/chrome_profile/` - 存储浏览器会话、cookies、登录信息等
- **下载文件**：`workspace/downloads/` - 存储下载的文件
- **日志文件**：`workspace/logs/` - 存储运行日志（可选）

首次运行时，脚本会自动创建这些目录。Chrome 用户数据目录可以保持登录状态，下次运行时无需重复登录。

### 脚本执行流程

1. ✅ 自动打开豆包网站
2. 🔍 检查登录状态
   - 如未登录，提示手动登录后按回车继续
3. 🎯 在底部菜单栏查找并点击"深入研究"
4. 📝 自动输入研究主题
5. 📤 发送研究请求
6. ⏳ 等待研究结果

### 研究主题

脚本会自动输入以下研究主题：

```
调用主流模型厂商提供深入研究功能，有没有这样一款产品，聚合这个功能就是一个输入调研主题分别调用这个模型厂商提供的深度研究能力
```

## 注意事项

1. **登录要求**：豆包需要登录才能使用深度研究功能，请确保手动完成登录
2. **网络连接**：确保网络连接稳定
3. **页面加载**：等待页面完全加载后再继续操作
4. **反爬虫**：脚本已添加反检测措施，但仍建议不要频繁运行

## 故障排除

### 找不到深入研究按钮

如果脚本无法找到深入研究按钮，可能的原因：
- 页面结构发生变化
- 需要先点击其他菜单项才能显示

解决方案：
- 手动查看页面元素，更新选择器
- 在脚本中添加更多等待时间

### ChromeDriver 版本不匹配

错误信息：`SessionNotCreatedException: Message: session not created: This version of ChromeDriver only supports Chrome version XX`

解决方案：
- 更新 ChromeDriver 到匹配版本
- 或使用 webdriver-manager 自动管理

### 输入框定位失败

如果无法找到输入框：
- 检查页面是否完全加载
- 确认是否在正确的聊天页面

## 自定义配置

### 修改研究主题

在 `input_research_topic` 方法中修改 `research_topic` 变量：

```python
research_topic = "您自定义的研究主题"
```

### 调整等待时间

可以根据网络情况调整各步骤的等待时间：

```python
time.sleep(5)  # 增加等待时间
```

## 安全提示

- 请妥善保管您的登录信息
- 不要在公共电脑上保存登录状态
- 脚本仅用于学习和研究目的

## 许可证

MIT License