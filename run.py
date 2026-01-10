#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
豆包深度研究自动化 - 简易启动脚本
"""

import sys
import os

def main():
    print("=" * 50)
    print("豆包深度研究自动化工具")
    print("=" * 50)
    print("\n请选择运行模式：")
    print("1. 自动模式（自动下载ChromeDriver）")
    print("2. 手动模式（使用系统PATH中的ChromeDriver）")
    print("3. 退出")
    print("-" * 50)

    choice = input("请输入选项 (1-3): ").strip()

    if choice == "1":
        # 自动模式
        print("\n🚀 启动自动模式...")
        from doubao_research_auto import DoubaoResearchAuto
        # 使用指定的工作区目录
        workspace_dir = os.path.join(os.path.dirname(__file__), "workspace")
        print(f"📁 工作区目录: {workspace_dir}")
        doubao = DoubaoResearchAuto(use_webdriver_manager=True, workspace_dir=workspace_dir)
        success = doubao.run()
        sys.exit(0 if success else 1)

    elif choice == "2":
        # 手动模式
        print("\n🔧 启动手动模式...")
        print("⚠️ 请确保已将ChromeDriver添加到系统PATH")
        from doubao_research_auto import DoubaoResearchAuto
        # 使用指定的工作区目录
        workspace_dir = os.path.join(os.path.dirname(__file__), "workspace")
        print(f"📁 工作区目录: {workspace_dir}")
        doubao = DoubaoResearchAuto(use_webdriver_manager=False, workspace_dir=workspace_dir)
        success = doubao.run()
        sys.exit(0 if success else 1)

    elif choice == "3":
        print("\n👋 再见！")
        sys.exit(0)

    else:
        print("\n❌ 无效的选项")
        sys.exit(1)

if __name__ == "__main__":
    main()