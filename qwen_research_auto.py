from playwright.sync_api import sync_playwright
import time
import sys
import os
import random

# Import config
import config

class QwenResearchAuto:
    def __init__(self, headless=False, workspace_dir=None):
        """初始化浏览器驱动"""
        # 确保目录存在
        config.ensure_dirs()

        self.workspace_dir = workspace_dir or config.WORKSPACE_DIR
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        self.setup_driver()
        self.base_url = "https://www.qianwen.com/"

    def setup_driver(self):
        """设置Playwright驱动"""
        try:
            print("🔧 正在启动 Playwright...")
            
            # 清理 Chromium 锁文件
            import glob
            for lock_pattern in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
                for lock_file in glob.glob(os.path.join(config.CHROME_PROFILE_DIR, lock_pattern)):
                    if os.path.lexists(lock_file):
                        try:
                            if os.path.islink(lock_file) or os.path.isfile(lock_file):
                                os.remove(lock_file)
                            elif os.path.isdir(lock_file):
                                import shutil
                                shutil.rmtree(lock_file)
                        except Exception:
                            pass

            self.playwright = sync_playwright().start()
            
            # 启动浏览器
            print(f"📁 Chrome 用户数据目录: {config.CHROME_PROFILE_DIR}")
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=config.CHROME_PROFILE_DIR,
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--window-size=1920,1080",
                    "--start-maximized"
                ],
                viewport=None,
                ignore_default_args=["--enable-automation"],
                downloads_path=config.SYSTEM_DOWNLOADS_DIR
            )
            
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            print("✅ 浏览器启动成功")

        except Exception as e:
            print(f"❌ 浏览器启动失败: {str(e)}")
            sys.exit(1)

    def visit_page(self):
        """访问通义千问页面"""
        try:
            print(f"\n🚀 正在访问通义千问页面: {self.base_url}")
            self.page.goto(self.base_url, wait_until="networkidle", timeout=60000)
            self.page.wait_for_timeout(5000)
            return True
        except Exception as e:
            print(f"❌ 页面访问失败: {str(e)}")
            return False

    def check_and_handle_login(self):
        """检查并处理登录"""
        try:
            print("\n🔍 检查登录状态...")

            # 检查登录按钮 (查找文字为"登录"的按钮)
            login_btn = self.page.get_by_role("button", name="登录").first
            
            if login_btn.is_visible():
                print("🔐 检测到需要登录")
                
                # 点击登录按钮
                print("🔘 点击登录按钮...")
                login_btn.click()
                self.page.wait_for_timeout(2000)

                # 查找弹窗中class前缀为StyledRight-tongyi-login-的元素
                print("🔍 查找登录弹窗...")
                # 使用CSS属性选择器匹配前缀
                login_modal = self.page.locator('[class^="StyledRight-tongyi-login-"]').first
                
                if login_modal.is_visible():
                    print("📸 找到登录弹窗，准备截图...")
                    
                    # 确保images目录存在
                    images_dir = os.path.join(self.workspace_dir, "images")
                    if not os.path.exists(images_dir):
                        os.makedirs(images_dir)
                    
                    # 生成文件名
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    screenshot_path = os.path.join(images_dir, f"qwen_login_modal_{timestamp}.png")
                    
                    # 截图并保存
                    login_modal.screenshot(path=screenshot_path)
                    print(f"✅ 登录弹窗截图已保存: {screenshot_path}")
                    
                    # 监控登录状态和二维码失效
                    print("\n⏳ 等待登录完成...")
                    max_wait = 300  # 5分钟超时
                    start_time = time.time()
                    
                    while time.time() - start_time < max_wait:
                        self.page.wait_for_timeout(2000)
                        
                        # 检查是否登录成功（弹窗消失）
                        if not login_modal.is_visible():
                            print("✅ 登录成功！")
                            return True
                        
                        # 检查二维码是否失效 (查找"立即刷新")
                        refresh_btn = self.page.get_by_text("立即刷新").first
                        
                        if refresh_btn.is_visible():
                            print("🔄 二维码已失效，尝试刷新...")
                            try:
                                refresh_btn.click()
                                print("🔘 点击刷新按钮...")
                                self.page.wait_for_timeout(2000)
                                
                                # 重新截图
                                timestamp = time.strftime("%Y%m%d_%H%M%S")
                                screenshot_path = os.path.join(images_dir, f"qwen_login_modal_refreshed_{timestamp}.png")
                                login_modal.screenshot(path=screenshot_path)
                                print(f"📸 新二维码已保存: {screenshot_path}")
                                
                            except Exception as e:
                                print(f"⚠️ 刷新二维码失败: {e}")
                        
                        elapsed = int(time.time() - start_time)
                        if elapsed % 30 == 0:
                            print(f"⏳ 等待登录中... ({elapsed}秒)")
                    
                    print("⚠️ 登录等待超时")
                    return False
                else:
                    print("⚠️ 未找到符合条件的登录弹窗")
                    return False
            else:
                print("✅ 未发现登录按钮，可能已登录")
                return True

        except Exception as e:
            print(f"⚠️ 登录处理异常: {str(e)}")
            return False

    def run(self):
        """运行完整流程"""
        success = False
        try:
            print("\n" + "=" * 60)
            print("🤖 通义千问深度研究自动化")
            print("=" * 60)

            if not self.visit_page(): return False
            if not self.check_and_handle_login(): return False
            
            # 这里暂时只实现到登录，后续可以添加研究功能
            print("\n✅ 登录流程执行完毕")
            
            print("\n" + "=" * 60)
            print("🎉 自动化流程完成！")
            print("=" * 60)
            success = True

        except KeyboardInterrupt:
            print("\n⚠️ 用户中断操作")
        except Exception as e:
            print(f"\n❌ 执行出错: {str(e)}")
        finally:
            self.cleanup(success)
        return success

    def cleanup(self, success):
        """清理资源"""
        try:
            if self.context:
                # self.context.close() 
                pass
            if success:
                print("\n🔚 任务完成！")
            else:
                print("\n💔 任务失败！")
        except:
            pass

if __name__ == "__main__":
    headless_env = os.environ.get("HEADLESS", "false").lower() == "true"
    qwen = QwenResearchAuto(headless=headless_env)
    success = qwen.run()
    print("\n📌 按任意键退出程序...")
    try:
        input()
    except KeyboardInterrupt:
        pass    
    if not success:
        sys.exit(1)
