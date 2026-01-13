#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置文件
"""

import os

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 工作区目录配置
WORKSPACE_DIR = os.path.join(PROJECT_ROOT, "workspace")

# Chrome 用户数据目录配置
CHROME_PROFILE_DIR = os.path.join(WORKSPACE_DIR, "chrome_profile")

# 下载目录配置（可选）
DOWNLOAD_DIR = os.path.join(WORKSPACE_DIR, "downloads")

# 系统下载目录配置（从环境变量获取用户目录）
SYSTEM_DOWNLOADS_DIR = os.path.join(os.environ.get("USERPROFILE", "C:\\Users\\Default"), "Downloads")

# 日志目录配置（可选）
LOG_DIR = os.path.join(WORKSPACE_DIR, "logs")

# 豆包网址配置
DOUBAO_URL = "https://www.doubao.com/chat/"

# 研究主题配置
RESEARCH_TOPIC = "调用主流模型厂商提供深入研究功能，有没有这样一款产品，聚合这个功能就是一个输入调研主题分别调用这个模型厂商提供的深度研究能力"

# 浏览器配置
BROWSER_CONFIG = {
    "window_size": (1920, 1080),
    "timeout": 30,
    "page_load_timeout": 60,
}

# 确保所有目录存在
def ensure_dirs():
    """确保所有配置的目录存在"""
    dirs = [WORKSPACE_DIR, CHROME_PROFILE_DIR, DOWNLOAD_DIR, LOG_DIR]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

if __name__ == "__main__":
    # 测试配置
    print("=" * 40)
    print("配置测试")
    print("=" * 40)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"工作区目录: {WORKSPACE_DIR}")
    print(f"Chrome配置目录: {CHROME_PROFILE_DIR}")
    ensure_dirs()
    print("✅ 所有目录创建成功")