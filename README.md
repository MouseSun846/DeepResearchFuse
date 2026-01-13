# 豆包深度研究自动化脚本 (Playwright 版)

这是一个使用 Python Playwright 实现的自动化脚本，用于访问豆包网站并执行深度研究功能。

## 功能特性

- 🌐 自动打开豆包网站
- 🔐 登录状态检测与引导 (支持二维码截图)
- 🎯 自动点击"深入研究"功能 (通过 "/" 命令)
- 📝 自动输入研究主题
- 📤 自动发送研究请求
- ⏳ 等待研究结果生成并自动下载 Markdown 结果
- � 支持 Docker 容器化运行

## 目录结构

```
.
├── doubao_research_auto.py     # Playwright 自动化脚本
├── config.py                  # 配置文件
├── requirements.txt           # 依赖包列表
├── Dockerfile                 # Docker 镜像构建文件
├── .dockerignore              # Docker 忽略文件
├── README.md                  # 说明文档
└── workspace/                 # 工作区目录
    ├── chrome_profile/         # 浏览器用户数据 (持久化登录)
    ├── images/                 # 存储二维码截图
    └── logs/                   # 日志目录
```

## 本地运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 运行脚本

```bash
python doubao_research_auto.py
```

## Docker 运行

### 1. 构建镜像

```bash
docker build -t deepsearchfuse:v1 .
```

### 2. 运行容器 (挂载持久化目录)

为了保持登录状态并获取下载的研究结果，建议挂载以下两个目录：

- **Chrome Profile**: 存储登录信息
- **Downloads**: 存储下载的 Markdown 结果

```bash
docker run --rm -it --user root -v ./workspace/chrome_profile:/app/workspace/chrome_profile -v ./workspace/downloads:/data/download  -v ./workspace/images:/app/workspace/images deepsearchfuse:v1
```

> [!NOTE]
> - `/app/workspace/chrome_profile` 是容器内存储浏览器数据的路径。
> - `/data/download` 是容器内默认的下载路径。

## 注意事项

1. **登录要求**：首次运行或 Session 失效时，脚本会截图二维码并保存到 `workspace/images/`。请扫描二维码完成登录。
2. **Headless 模式**：在 Docker 中运行时默认使用 Headless 模式。
3. **下载路径**：下载的 Markdown 结果将自动保存到 `SYSTEM_DOWNLOADS_DIR` 配置的路径。

## 许可证

MIT License