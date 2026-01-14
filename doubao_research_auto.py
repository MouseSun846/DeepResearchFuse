from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, Locator
import time
import sys
import os
import shutil
import random

# Import config
import config

class DoubaoResearchAuto:
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
        self.base_url = config.DOUBAO_URL

    def setup_driver(self):
        """设置Playwright驱动"""
        try:
            print("🔧 正在启动 Playwright...")
            
            # 清理 Chromium 锁文件，防止 "profile in use" 错误
            import glob
            for lock_pattern in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
                for lock_file in glob.glob(os.path.join(config.CHROME_PROFILE_DIR, lock_pattern)):
                    if os.path.lexists(lock_file):
                        print(f"🧹 发现旧的锁文件，正在清理: {lock_file}")
                        try:
                            if os.path.islink(lock_file) or os.path.isfile(lock_file):
                                os.remove(lock_file)
                            elif os.path.isdir(lock_file):
                                import shutil
                                shutil.rmtree(lock_file)
                        except Exception as e:
                            print(f"⚠️ 清理锁文件失败: {e}")

            self.playwright = sync_playwright().start()
            
            # 启动浏览器，使用用户数据目录以持久化登录
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
                viewport=None,  # 让浏览器窗口决定视口大小
                ignore_default_args=["--enable-automation"],
                downloads_path=config.SYSTEM_DOWNLOADS_DIR
            )
            
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            print("✅ 浏览器启动成功")

        except Exception as e:
            print(f"❌ 浏览器启动失败: {str(e)}")
            print("\n💡 解决方案：")
            print("1. 安装 Playwright: pip install playwright")
            print("2. 安装浏览器: playwright install chromium")
            sys.exit(1)

    def visit_page(self):
        """访问豆包页面"""
        try:
            print(f"\n🚀 正在访问豆包页面: {self.base_url}")
            self.page.goto(self.base_url, wait_until="networkidle", timeout=60000)

            # 等待页面加载
            print("⏳ 等待页面加载完成...")
            self.page.wait_for_timeout(5000)

            # 检查页面是否正确加载
            current_url = self.page.url
            if "doubao.com" in current_url:
                print("✅ 页面加载成功")
                return True
            else:
                print(f"⚠️ 页面重定向至: {current_url}")
                return True  # 可能跳转到登录页，这是正常的

        except Exception as e:
            print(f"❌ 页面访问失败: {str(e)}")
            return False

    def _capture_qr_code(self, images_dir):
        """截图二维码并保存到指定目录"""
        try:
            # 等待二维码容器或内容加载
            # 豆包的二维码通常是一个 canvas 或 img
            qr_selectors = [
                "#semi-modal-body > div > div",
            ]
            
            qr_element = None
            for selector in qr_selectors:
                element = self.page.locator(selector).first
                if element.is_visible():
                    qr_element = element
                    break
            
            if qr_element:
                # 生成文件名
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                qr_path = os.path.join(images_dir, f"qr_code_{timestamp}.png")
                
                # 截图并保存
                qr_element.screenshot(path=qr_path)
                print(f"📸 二维码截图已保存: {qr_path}")
                return qr_path
            else:
                print("⚠️ 未找到可见的二维码元素")
                # 截图整个模态框作为参考
                modal = self.page.locator("#semi-modal-body").first
                if modal.is_visible():
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    modal_path = os.path.join(images_dir, f"modal_debug_{timestamp}.png")
                    modal.screenshot(path=modal_path)
                    print(f"📸 已截图整个登录框用于调试: {modal_path}")
                return None
        except Exception as e:
            print(f"⚠️ 二维码截图失败: {str(e)}")
            return None

    def check_and_handle_login(self):
        """检查并处理登录"""
        try:
            print("\n🔍 检查登录状态...")

            # 多种登录状态检测方式
            login_indicators = [
                "text=登录",
                "text=请登录",
                "text=登录后使用",
                ".avatar",
                ".user"
            ]

            # 等待其中一个指示器出现
            login_status = "unknown"
            for indicator in login_indicators:
                if self.page.locator(indicator).first.is_visible():
                    if "登录" in indicator:
                        login_status = "需要登录"
                    else:
                        login_status = "已登录"
                    break

            if login_status == "需要登录":
                print("\n" + "=" * 50)
                print("🔐 检测到需要登录")
                print("=" * 50)

                # 点击登录按钮
                login_button = self.page.get_by_role("button", name="登录").first
                if not login_button.is_visible():
                    login_button = self.page.locator("text=登录").first

                if login_button.is_visible():
                    print("🔘 点击登录按钮...")
                    login_button.click()
                    
                    # 等待登录模态框出现
                    try:
                        self.page.locator("#semi-modal-body").wait_for(state="visible", timeout=10000)
                        print("✅ 登录模态框已显示")
                    except:
                        print("⚠️ 登录模态框未在预期时间内显示")

                    self.page.wait_for_timeout(2000)
                    
                    # 尝试多种可能的选择器
                    # 使用 XPath 定位并通过 JS 点击二维码切换按钮
                    qr_xpath = '//*[@id="semi-modal-body"]/div/div/div/div/div/div[1]/div'
                    clicked = False
                    
                    try:
                        print(f"🔘 使用 XPath 定位二维码切换按钮: {qr_xpath}")
                        # 通过 XPath 定位元素
                        qr_show_btn = self.page.locator(f"xpath={qr_xpath}")
                        qr_show_btn.wait_for(state="attached", timeout=5000)
                        
                        # 使用 JS 脚本点击
                        print("🔘 使用 JS 脚本点击...")
                        self.page.evaluate('''
                            () => {
                                const result = document.evaluate(
                                    '//*[@id="semi-modal-body"]/div/div/div/div/div/div[1]/div',
                                    document,
                                    null,
                                    XPathResult.FIRST_ORDERED_NODE_TYPE,
                                    null
                                );
                                const element = result.singleNodeValue;
                                if (element) {
                                    element.click();
                                    return true;
                                }
                                return false;
                            }
                        ''')
                        
                        self.page.wait_for_timeout(2000)
                        clicked = True
                        print("✅ 已触发显示二维码操作")
                    except Exception as e:
                        print(f"⚠️ 点击二维码切换按钮失败: {e}")
                    
                    if clicked:
                        print("⏳ 等待二维码显示...")
                        try:
                            # 等待二维码元素出现
                            self.page.locator("#semi-modal-body canvas, #semi-modal-body img").first.wait_for(state="visible", timeout=10000)
                            print("✅ 二维码已显示")
                        except:
                            print("⚠️ 等待二维码显示超时")
                    
                    if not clicked:
                        print("⚠️ 未找到或无法点击二维码切换按钮，尝试直接检测二维码...")
                        if self.page.locator("#semi-modal-body canvas, #semi-modal-body img").first.is_visible():
                            print("ℹ️ 二维码似乎已经显示")
                
                # 确保 images 目录存在
                images_dir = os.path.join(self.workspace_dir, "images")
                os.makedirs(images_dir, exist_ok=True)
                
                # 截图二维码并保存
                print("📸 正在截取二维码...")
                qr_saved = self._capture_qr_code(images_dir)
                
                if qr_saved:
                    print(f"📱 请扫描二维码登录，二维码已保存到: {qr_saved}")
                
                # 监控登录状态和二维码失效
                print("\n⏳ 等待登录完成...")
                max_wait = 7200  # 2小时超时
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    self.page.wait_for_timeout(2000)
                    
                    # 检查是否登录成功（弹窗消失）
                    modal = self.page.locator("#semi-modal-body")
                    if not modal.is_visible():
                        print("✅ 登录成功！")
                        return True
                    
                    # 检查二维码是否失效
                    qr_image = self.page.locator('[data-testid="qrcode_image"]')
                    expired_indicator = self.page.locator('xpath=//*[@id="semi-modal-body"]/div/div/div/div/div/div[2]/div[1]/div/div[2]')
                    
                    if expired_indicator.is_visible() and "失效" in (expired_indicator.text_content() or ""):
                        print("🔄 二维码已失效，尝试刷新...")
                        
                        refreshed = False
                        # 策略1: 获取二维码中心坐标并点击 (最可靠)
                        try:
                            if qr_image.is_visible():
                                box = qr_image.bounding_box()
                                if box:
                                    x = box['x'] + box['width'] / 2
                                    y = box['y'] + box['height'] / 2
                                    print(f"📍 点击二维码中心坐标: ({x}, {y})")
                                    self.page.mouse.click(x, y)
                                    refreshed = True
                        except Exception as e:
                            print(f"⚠️ 坐标点击失败: {e}")

                        # 策略2: 如果坐标点击失败，尝试点击遮罩层
                        if not refreshed:
                            try:
                                print("🔘 尝试点击失效遮罩层...")
                                self.page.locator('xpath=//*[@id="semi-modal-body"]/div/div/div/div/div/div[2]/div[1]/div/div[1]').click(force=True)
                                refreshed = True
                            except Exception as e:
                                print(f"⚠️ 遮罩层点击失败: {e}")

                        self.page.wait_for_timeout(3000)
                        qr_saved = self._capture_qr_code(images_dir)
                        if qr_saved:
                            print(f"📱 新二维码已保存到: {qr_saved}")
                    
                    elapsed = int(time.time() - start_time)
                    if elapsed % 30 == 0:
                        print(f"⏳ 等待登录中... ({elapsed}秒)")
                
                print("⚠️ 登录等待超时")
                return False

            elif login_status == "已登录":
                print("✅ 检测到已登录状态")
                return True
            else:
                print("⚠️ 无法确定登录状态，继续执行...")
                return True

        except Exception as e:
            print(f"⚠️ 登录检查异常: {str(e)}")
            return True

    def input_topic(self):
        """输入研究主题"""
        try:
            print("\n🔄 刷新页面...")
            self.page.wait_for_timeout(3000)
            self.page.reload(wait_until="networkidle")
            self.page.wait_for_timeout(5000)
            
            print("\n📝 准备输入研究主题...")
            topic = config.RESEARCH_TOPIC.replace("/", "")
            print(f"📋 研究主题: {topic}")

            # 输入框定位
            input_selector = "textarea[placeholder*='发消息'], textarea.text-area, div[contenteditable='true']"
            input_element = self.page.locator(input_selector).first
            
            if not input_element.is_visible():
                print("❌ 未找到输入框")
                return False

            # 模拟人类操作：移动鼠标并点击
            box = input_element.bounding_box()
            if box:
                self.page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                self.page.wait_for_timeout(random.randint(500, 1000))
                self.page.mouse.down()
                self.page.wait_for_timeout(random.randint(50, 150))
                self.page.mouse.up()
            else:
                input_element.click()
            
            # 清空并输入 "/" (模拟打字)
            print("⌨️  输入 '/' 命令...")
            input_element.clear()
            self.page.wait_for_timeout(random.randint(500, 1000))
            input_element.type("/", delay=random.randint(100, 300))
            self.page.wait_for_timeout(3000)

            # 查找并点击 "深入研究" 选项
            print("🔍 查找 '深入研究' 选项...")
            research_option = self.page.locator("text=深入研究").first
            if research_option.is_visible():
                # 移动鼠标到选项并点击
                box = research_option.bounding_box()
                if box:
                    self.page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2, steps=5)
                    self.page.wait_for_timeout(random.randint(300, 800))
                    self.page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                else:
                    research_option.click()
                print("✅ 选择 '深入研究' 选项")
                self.page.wait_for_timeout(3000)
            else:
                print("⚠️  未找到 '深入研究' 选项，直接输入主题")

            # 输入主题 (模拟打字)
            print(f"⌨️  输入主题: {topic}")
            input_element.type(topic, delay=random.randint(50, 150))

            print(f"✅ 成功输入主题")
            self.page.wait_for_timeout(random.randint(2000, 4000))
            return True

        except Exception as e:
            print(f"❌ 输入主题失败: {str(e)}")
            return False

    def wait_and_click_start_research(self):
        """等待并点击开始研究按钮"""
        try:
            print("\n🔍 等待开始研究按钮出现...")
            # 尝试多种选择器，优先使用 data-testid
            selectors = [
                'div[data-testid="suggest_message_item"]',
                "button:has-text('直接开始研究')",
            ]
            
            start_time = time.time()
            timeout = 60000  # 60秒超时
            
            while time.time() - start_time < timeout:
                start_btn = None
                for selector in selectors:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        start_btn = element
                        print(f"✅ 找到按钮，使用选择器: {selector}")
                        break
                
                if start_btn:
                    print("🎯 点击'开始研究'按钮...")
                    # 模拟鼠标移动并点击
                    box = start_btn.bounding_box()
                    if box:
                        self.page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2, steps=5)
                        self.page.wait_for_timeout(random.randint(200, 500))
                        self.page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                    else:
                        start_btn.click()
                    
                    print("✅ 成功点击'开始研究'按钮")
                    self.page.wait_for_timeout(2000)
                    return True
                
                # 等待一小段时间后重试
                self.page.wait_for_timeout(1000)
            
            print("⚠️ 未找到'开始研究'按钮，尝试查找页面上所有按钮...")
            # 调试：打印所有可见按钮文本
            buttons = self.page.locator("button, div[role='button'], div[data-testid='suggest_message_item']").all()
            visible_buttons = [btn.text_content() for btn in buttons if btn.is_visible()]
            print(f"🔘 当前页面可见按钮: {visible_buttons}")
            
            # 截图保存现场
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            debug_path = os.path.join(self.workspace_dir, "images", f"debug_start_research_{timestamp}.png")
            self.page.screenshot(path=debug_path)
            print(f"📸 已保存调试截图: {debug_path}")
            
            return True
            
        except Exception as e:
            print(f"⚠️ 处理开始研究按钮时异常: {str(e)}")
            return True

    def send_request(self):
        """发送研究请求"""
        try:
            print("\n📤 准备发送研究请求...")
            # 查找发送按钮
            send_btn = self.page.locator('[data-testid="chat_input_send_button"]').first
            
            if send_btn.is_visible():
                # 模拟鼠标移动到发送按钮
                box = send_btn.bounding_box()
                if box:
                    # 平滑移动鼠标
                    self.page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2, steps=10)
                    self.page.wait_for_timeout(random.randint(500, 1500))
                    self.page.mouse.down()
                    self.page.wait_for_timeout(random.randint(50, 150))
                    self.page.mouse.up()
                else:
                    send_btn.click()
                    
                print("🎯 成功点击发送按钮")
                self.page.wait_for_timeout(1000)
                return True
            else:
                print("⚠️ 未找到发送按钮，尝试 Enter 键...")
                self.page.keyboard.press("Enter")
                return True

        except Exception as e:
            print(f"❌ 发送失败: {str(e)}")
            return False

    def monitor_results(self):
        """监控研究结果生成"""
        try:
            print("\n⏳ 等待研究结果生成...")
            print("🔄 这可能需要几分钟，请耐心等待...")

            # 语音输入按钮检测（研究完成的标志）
            asr_btn = self.page.locator("[data-testid='asr_btn']")
            
            start_time = time.time()
            max_wait = 7200  # 2小时
            
            try:
                asr_btn.wait_for(state="visible", timeout=max_wait * 1000)
                print(f"✅ 研究完成（总等待时间: {int(time.time() - start_time)}秒）")
            except:
                print("\n⚠️ 等待超时，但研究可能仍在进行")
                return True

            # 检测结果区域
            print("⏳ 正在检测研究结果...")
            result_card = self.page.locator("[data-testid='doc_card'], .flow-product-card").first
            
            if result_card.is_visible():
                print("✅ 找到研究结果卡片")
                result_card.click()
                print("🔘 点击研究结果卡片")
                self.page.wait_for_timeout(10000)  # 等待侧边栏加载
                
                # 尝试下载
                download_btn = self.page.locator("text=下载").first
                if download_btn.is_visible():
                    download_btn.click()
                    self.page.wait_for_timeout(2000)
                    
                    markdown_opt = self.page.locator("text=Markdown").first
                    if markdown_opt.is_visible():
                        with self.page.expect_download() as download_info:
                            markdown_opt.click()
                        download = download_info.value
                        
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        target_path = os.path.join(self.workspace_dir, f"research_result_{timestamp}.md")
                        download.save_as(target_path)
                        print(f"📁 研究结果已保存到: {target_path}")
                    else:
                        print("⚠️ 未找到 Markdown 选项")
                else:
                    print("⚠️ 未找到下载按钮")
            
            return True

        except Exception as e:
            print(f"⚠️ 等待结果时异常: {str(e)}")
            return True

    def run(self):
        """运行完整流程"""
        success = False
        try:
            print("\n" + "=" * 60)
            print("🤖 豆包深度研究自动化 (Playwright 版)")
            print("=" * 60)

            if not self.visit_page(): return False
            if not self.check_and_handle_login(): return False
            if not self.input_topic(): return False
            if not self.send_request(): return False
            self.wait_and_click_start_research()
            self.monitor_results()

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
                # self.context.close() # 保持打开以便查看
                pass
            if self.playwright:
                # self.playwright.stop()
                pass
            if success:
                print("\n🔚 任务完成！")
            else:
                print("\n💔 任务失败！")
        except:
            pass

if __name__ == "__main__":
    # 从环境变量读取 headless 配置，默认为 False (本地运行通常需要界面)
    # 在 Docker 中可以通过 ENV HEADLESS=true 设置
    headless_env = os.environ.get("HEADLESS", "false").lower() == "true"
    doubao = DoubaoResearchAuto(headless=headless_env)
    success = doubao.run()
    # print("\n📌 按任意键退出程序...")
    # try:
    #     input()
    # except KeyboardInterrupt:
    #     pass
    if not success:
        sys.exit(1)