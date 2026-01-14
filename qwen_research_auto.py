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
        self.base_url = "https://www.qianwen.com/chat/"

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
            
            # 授予剪贴板权限
            self.context.grant_permissions(["clipboard-read", "clipboard-write"])
            
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

    def input_topic(self):
        """输入研究主题"""
        try:
            print("\n📝 准备输入研究主题...")
            
            # 查找并点击 "深度研究" 按钮
            print("🔍 查找 '深度研究' 按钮...")
            deep_research_btn = self.page.get_by_text("深度研究", exact=True).first
            # 也可以尝试: self.page.get_by_role("button", name="深度研究")
            
            if deep_research_btn.is_visible():
                print("🔘 点击 '深度研究' 按钮...")
                deep_research_btn.click()
                self.page.wait_for_timeout(2000)
            else:
                print("⚠️ 未找到 '深度研究' 按钮，尝试直接输入...")

            # 查找输入框 (class包含 ant-input)
            print("🔍 查找输入框...")
            # 使用CSS选择器匹配class包含ant-input的元素
            input_element = self.page.locator('.ant-input').first
            
            if input_element.is_visible():
                topic = config.RESEARCH_TOPIC
                print(f"⌨️ 准备输入主题: {topic}")
                
                # 模拟人类操作：移动鼠标并点击
                box = input_element.bounding_box()
                if box:
                    # 移动到输入框中心
                    self.page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                    self.page.wait_for_timeout(random.randint(500, 1000))
                    self.page.mouse.down()
                    self.page.wait_for_timeout(random.randint(50, 150))
                    self.page.mouse.up()
                else:
                    input_element.click()
                
                # 清空输入框 (如果需要)
                input_element.clear()
                self.page.wait_for_timeout(random.randint(500, 1000))
                
                # 模拟打字输入
                print(f"⌨️ 正在输入主题 (模拟打字)...")
                input_element.type(topic, delay=random.randint(50, 150))
                self.page.wait_for_timeout(random.randint(1000, 2000))
                
                # 模拟回车发送
                print("Go 🚀 发送...")
                self.page.keyboard.press("Enter")
                
                return True
            else:
                print("❌ 未找到输入框")
                return False

        except Exception as e:
            print(f"❌ 输入主题失败: {str(e)}")
            return False

    def wait_for_completion(self):
        """等待研究完成"""
        try:
            print("\n⏳ 等待研究完成...")
            print("🔄 这可能需要较长时间，请耐心等待...")
            
            # 给一点时间让"终止任务"按钮出现
            self.page.wait_for_timeout(5000)
            
            start_time = time.time()
            max_wait = 7200  # 2小时超时
            stop_btn_appeared = False
            
            while time.time() - start_time < max_wait:
                self.page.wait_for_timeout(5000)
                
                # 查找iframe
                iframe = self.page.frame_locator("#deep-research-iframe")
                
                # 在iframe中查找 "终止任务" 按钮
                stop_btn = iframe.get_by_text("终止任务").first
                
                # 查找 "直接开始研究" 按钮 (通常在主页面，但也可能在iframe中，这里先查主页面)
                start_research_btn = self.page.get_by_text("直接开始研究").first
                
                if start_research_btn.is_visible():
                    print("🔘 发现 '直接开始研究' 按钮，点击...")
                    start_research_btn.click()
                    self.page.wait_for_timeout(2000)
                    continue
                
                if stop_btn.is_visible():
                    stop_btn_appeared = True
                    # 仍在生成中
                    elapsed = int(time.time() - start_time)
                    if elapsed % 30 == 0:
                        print(f"⏳ 研究进行中... ({elapsed}秒)")
                else:
                    if stop_btn_appeared:
                        # "终止任务" 按钮曾经出现过，现在消失了，说明完成
                        print(f"✅ 研究完成！(总耗时: {int(time.time() - start_time)}秒)")
                        return True
                    else:
                        # "终止任务" 按钮还没出现，可能还在准备中
                        elapsed = int(time.time() - start_time)
                        if elapsed % 10 == 0:
                            print(f"⏳ 等待任务开始... ({elapsed}秒)")
            
            print("⚠️ 等待超时，研究可能仍在进行或已失败")
            return False

        except Exception as e:
            print(f"⚠️ 等待结果时异常: {str(e)}")
            return False

    def save_results(self):
        """保存研究结果"""
        try:
            print("\n💾 准备保存研究结果...")
            
            # 刷新页面
            print("🔄 刷新页面...")
            self.page.reload()
            self.page.wait_for_timeout(5000)
            
            # 查找下载图标按钮
            # data-icon-type="qwpcicon-down"
            print("🔍 查找下载按钮...")
            download_btn = self.page.locator('span[data-icon-type="qwpcicon-down"]').first
            
            if download_btn.is_visible():
                # 移动鼠标到按钮中心
                box = download_btn.bounding_box()
                if box:
                    print("🖱️ 移动鼠标到下载按钮...")
                    self.page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                    self.page.wait_for_timeout(2000)
                    
                    # 等待弹窗出现
                    print("⏳ 等待选项弹窗...")
                    # 查找 "复制为Markdown" 选项
                    copy_option = self.page.get_by_text("复制为Markdown").first
                    
                    if copy_option.is_visible():
                        print("🔘 点击 '复制为Markdown'...")
                        copy_option.click()
                        self.page.wait_for_timeout(1000)
                        
                        # 获取剪贴板内容
                        print("📋 读取剪贴板内容...")
                        content = self.page.evaluate("navigator.clipboard.readText()")
                        
                        if content:
                            # 保存到文件
                            timestamp = time.strftime("%Y%m%d_%H%M%S")
                            filename = f"qwen_research_{timestamp}.md"
                            
                            # 优先使用 SYSTEM_DOWNLOADS_DIR，如果不存在则使用 DOWNLOAD_DIR
                            save_dir = config.SYSTEM_DOWNLOADS_DIR
                            if not os.path.exists(save_dir):
                                try:
                                    os.makedirs(save_dir)
                                except:
                                    save_dir = config.DOWNLOAD_DIR
                                    os.makedirs(save_dir, exist_ok=True)
                            
                            filepath = os.path.join(save_dir, filename)
                            with open(filepath, "w", encoding="utf-8") as f:
                                f.write(content)
                            
                            print(f"✅ 结果已保存到: {filepath}")
                            return True
                        else:
                            print("⚠️ 剪贴板为空")
                    else:
                        print("⚠️ 未找到 '复制为Markdown' 选项")
                else:
                    print("⚠️ 无法获取下载按钮位置")
            else:
                print("⚠️ 未找到下载按钮")
                
            return False
            
        except Exception as e:
            print(f"❌ 保存结果失败: {str(e)}")
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
            if not self.input_topic(): return False
            self.wait_for_completion()
            self.save_results()
            
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
