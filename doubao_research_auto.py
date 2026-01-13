from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import sys
import os
import shutil

# Import config
import config

# Try to import webdriver-manager, will use if available
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

class DoubaoResearchAuto:
    def __init__(self, use_webdriver_manager=True, workspace_dir=None):
        """初始化浏览器驱动"""
        # 确保目录存在
        config.ensure_dirs()

        self.workspace_dir = workspace_dir or config.WORKSPACE_DIR
        self.setup_driver(use_webdriver_manager)
        self.wait = WebDriverWait(self.driver, config.BROWSER_CONFIG["timeout"])
        self.base_url = config.DOUBAO_URL

    def setup_driver(self, use_webdriver_manager):
        """设置Chrome驱动"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 添加 user-data-dir 配置
        chrome_options.add_argument(f"--user-data-dir={config.CHROME_PROFILE_DIR}")
        print(f"📁 Chrome 用户数据目录: {config.CHROME_PROFILE_DIR}")

        # 添加更多反检测选项
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        try:
            if use_webdriver_manager and WEBDRIVER_MANAGER_AVAILABLE:
                print("🔧 使用 webdriver-manager 自动管理 ChromeDriver")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # 尝试使用系统 PATH 中的 chromedriver
                print("🔧 使用系统路径中的 ChromeDriver")
                self.driver = webdriver.Chrome(options=chrome_options)

            self.driver.maximize_window()
            print("✅ 浏览器启动成功")

        except Exception as e:
            print(f"❌ 浏览器启动失败: {str(e)}")
            print("\n💡 解决方案：")
            print("1. 安装 webdriver-manager: pip install webdriver-manager")
            print("2. 或手动下载 ChromeDriver 并添加到 PATH")
            sys.exit(1)

    def visit_page(self):
        """访问豆包页面"""
        try:
            print(f"\n🚀 正在访问豆包页面: {self.base_url}")
            self.driver.get(self.base_url)

            # 等待页面加载
            print("⏳ 等待页面加载完成...")
            time.sleep(5)

            # 检查页面是否正确加载
            current_url = self.driver.current_url
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
            # 定位二维码容器
            qr_container = self.driver.find_element(
                By.CSS_SELECTOR, 
                "#semi-modal-body > div > div > div"
            )
            
            if qr_container.is_displayed():
                # 生成文件名
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                qr_path = os.path.join(images_dir, f"qr_code_{timestamp}.png")
                
                # 截图并保存
                qr_container.screenshot(qr_path)
                print(f"📸 二维码截图已保存: {qr_path}")
                return qr_path
            else:
                print("⚠️ 二维码容器不可见")
                return None
        except Exception as e:
            print(f"⚠️ 二维码截图失败: {str(e)}")
            return None


    def check_and_handle_login(self):
        """检查并处理登录"""
        try:
            print("\n🔍 检查登录状态...")

            # 多种登录状态检测方式
            login_checks = [
                # 检查是否有登录按钮
                ("//button[contains(text(), '登录')]", "需要登录"),
                ("//a[contains(text(), '登录')]", "需要登录"),
                ("//span[contains(text(), '登录')]", "需要登录"),
                # 检查是否有登录提示
                ("//div[contains(text(), '请登录')]", "需要登录"),
                ("//div[contains(text(), '登录后使用')]", "需要登录"),
                # 检查是否已登录（有用户头像或用户名）
                ("//div[contains(@class, 'avatar')]", "已登录"),
                ("//div[contains(@class, 'user')]", "已登录"),
            ]

            login_status = "unknown"
            for xpath, status in login_checks:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    if elements and any(elem.is_displayed() for elem in elements):
                        login_status = status
                        break
                except:
                    continue

            if "需要登录" in login_status:
                print("\n" + "=" * 50)
                print("🔐 检测到需要登录")
                print("=" * 50)

                # 点击登录按钮
                login_button = None
                login_button_strategies = [
                    "//button[contains(text(), '登录')]",
                    "//a[contains(text(), '登录')]",
                    "//span[contains(text(), '登录')]",
                    "//*[contains(@class, 'login') and (self::button or self::a)]",
                ]
                
                for strategy in login_button_strategies:
                    try:
                        elements = self.driver.find_elements(By.XPATH, strategy)
                        for elem in elements:
                            if elem.is_displayed() and elem.is_enabled():
                                login_button = elem
                                break
                        if login_button:
                            break
                    except:
                        continue
                
                if login_button:
                    print("🔘 点击登录按钮...")
                    try:
                        login_button.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", login_button)
                    time.sleep(3)  # 等待弹窗出现
                    
                    # 点击显示二维码按钮
                    print("🔘 点击显示二维码按钮...")
                    try:
                        qr_show_btn = self.driver.find_element(
                            By.CSS_SELECTOR,
                            '[data-testid="qrcode_switcher"]'
                        )
                        if qr_show_btn.is_displayed():
                            # 使用 JavaScript 点击，更可靠
                            self.driver.execute_script("arguments[0].click();", qr_show_btn)
                            time.sleep(2)  # 等待二维码加载
                            print("✅ 已点击显示二维码按钮")
                    except Exception as e:
                        print(f"⚠️ 点击显示二维码按钮失败: {str(e)}")
                else:
                    print("⚠️ 未找到登录按钮")
                
                # 确保 images 目录存在
                images_dir = os.path.join(self.workspace_dir, "images")
                os.makedirs(images_dir, exist_ok=True)
                
                # 截图二维码并保存
                qr_saved = self._capture_qr_code(images_dir)
                
                if qr_saved:
                    print(f"📱 请扫描二维码登录，二维码已保存到: {qr_saved}")
                
                # 监控登录状态和二维码失效
                print("\n⏳ 等待登录完成...")
                max_wait = 300  # 5分钟超时
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    time.sleep(2)
                    
                    # 检查是否登录成功（弹窗消失）
                    try:
                        modal = self.driver.find_element(By.CSS_SELECTOR, "#semi-modal-body")
                        if not modal.is_displayed():
                            print("✅ 登录成功！")
                            return True
                    except:
                        # 弹窗不存在，可能已登录成功
                        print("✅ 登录成功！")
                        return True
                    
                    # 检查二维码是否失效
                    try:
                        expired_indicator = self.driver.find_element(
                            By.CSS_SELECTOR, 
                            "#semi-modal-body div.cover-kIII0c p"
                        )
                        if expired_indicator.is_displayed() and "失效" in expired_indicator.text:
                            print("🔄 二维码已失效，点击刷新...")
                            
                            # 点击刷新二维码
                            refresh_area = self.driver.find_element(
                                By.CSS_SELECTOR,
                                "#semi-modal-body div.cover-kIII0c"
                            )
                            refresh_area.click()
                            time.sleep(2)  # 等待新二维码加载
                            
                            # 重新截图
                            qr_saved = self._capture_qr_code(images_dir)
                            if qr_saved:
                                print(f"📱 新二维码已保存到: {qr_saved}")
                    except:
                        pass  # 没有失效提示，继续等待
                    
                    elapsed = int(time.time() - start_time)
                    if elapsed % 30 == 0:
                        print(f"⏳ 等待登录中... ({elapsed}秒)")
                
                print("⚠️ 登录等待超时")
                return False

            elif "已登录" in login_status:
                print("✅ 检测到已登录状态")
                return True
            else:
                print("⚠️ 无法确定登录状态，继续执行...")
                return True

        except Exception as e:
            print(f"⚠️ 登录检查异常: {str(e)}")
            return True

    def find_and_click_research(self):
        """查找并点击深入研究功能"""
        try:
            print("\n🔍 查找'深入研究'功能...")

            # 先滚动到底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # 多种方式定位研究功能
            research_strategies = [
                # 基于测试发现的具体研究功能按钮
                "//button[contains(text(), '深度思考')]",  # 深度思考按钮
                "//button[contains(text(), 'AI 作图')]",  # AI 作图按钮
                "//button[contains(text(), '写稿助手')]",  # 写稿助手按钮
                "//button[contains(text(), '编程')]",  # 编程按钮
                "//button[contains(text(), '更多功能')]",  # 更多功能按钮

                # 直接文本匹配（通用研究功能）
                "//button[contains(text(), '深入研究')]",
                "//div[contains(text(), '深入研究')]",
                "//span[contains(text(), '深入研究')]",

                # 模糊匹配
                "//*[contains(text(), '研究') and not(contains(text(), '研究结果'))]",
                "//*[contains(@title, '研究')]",

                # 类名匹配
                "//*[contains(@class, 'research')]",
                "//*[contains(@class, 'deep-research')]",
                "//*[contains(@class, 'study')]",

                # 角色属性匹配
                "//div[@role='button' and contains(., '研究')]",
                "//button[@role='button' and contains(., '研究')]",
            ]

            research_element = None
            for strategy in research_strategies:
                try:
                    elements = self.driver.find_elements(By.XPATH, strategy)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            # 验证元素文本确实包含"研究"
                            elem_text = elem.text or elem.get_attribute('title') or elem.get_attribute('aria-label')
                            if elem_text and ('研究' in elem_text or 'research' in elem_text.lower()):
                                research_element = elem
                                print(f"✅ 找到研究功能: {elem_text}")
                                break
                    if research_element:
                        break
                except:
                    continue

            if research_element:
                # 尝试点击
                try:
                    # 滚动到元素位置
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", research_element)
                    time.sleep(1)

                    # 鼠标悬停以确保可点击
                    ActionChains(self.driver).move_to_element(research_element).perform()
                    time.sleep(0.5)

                    # 点击元素
                    research_element.click()
                    print("🎯 成功点击'深入研究'")
                    time.sleep(2)
                    return True

                except Exception as e:
                    # 使用 JavaScript 点击
                    print(f"⚠️ 普通点击失败: {str(e)}")
                    self.driver.execute_script("arguments[0].click();", research_element)
                    print("🎯 使用 JavaScript 成功点击")
                    time.sleep(2)
                    return True
            else:
                print("❌ 未能找到'深入研究'功能")
                print("💡 请确认：")
                print("1. 是否在正确的聊天页面")
                print("2. 页面是否包含深度研究功能")
                return False

        except Exception as e:
            print(f"❌ 查找研究功能失败: {str(e)}")
            return False

    def input_topic(self):
        """输入研究主题"""
        try:
            print("\n📝 准备输入研究主题...")

            # 使用配置中的研究主题，确保不包含斜杠
            topic = config.RESEARCH_TOPIC
            # 清理主题中的斜杠，确保不包含命令符号
            topic = topic.replace("/", "")
            print(f"📋 研究主题（已清理斜杠）: {topic}")

            # 输入框定位策略
            input_strategies = [
                # 基于测试发现的textarea输入框
                "//textarea[@placeholder='发消息或输入“/”选择技能']",  # 匹配具体占位符
                "//textarea[contains(@class, 'c18422e05') and contains(@class, 'f11b1c66')]",  # 匹配特定类名
                "//textarea[contains(@placeholder, '发消息')]",  # 匹配占位符包含"发消息"
                "//textarea[contains(@class, 'text-area')]",  # 通用文本区域
                "//textarea[not(@disabled)]",  # 所有可用的textarea

                # contenteditable div
                "//div[@contenteditable='true' and contains(@class, 'input')]",
                "//div[@contenteditable='true' and not(contains(@class, 'output'))]",
                "//div[@contenteditable='true']",

                # input 元素
                "//input[@type='text' and not(@readonly)]",
                "//input[contains(@placeholder, '输入')]",

                # 通用容器
                "//*[contains(@class, 'input') and contains(@class, 'textarea')]",
                "//*[contains(@class, 'input') and not(contains(@class, 'disabled'))]",
            ]

            input_element = None
            for strategy in input_strategies:
                try:
                    elements = self.driver.find_elements(By.XPATH, strategy)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            input_element = elem
                            print(f"✅ 找到输入框")
                            break
                    if input_element:
                        break
                except:
                    continue

            if not input_element:
                print("❌ 未找到输入框")
                # 尝试查找整个输入区域
                print("🔍 尝试查找输入区域...")
                area_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'input-area') or contains(@class, 'chat-input')]")
                if area_elements:
                    print("💡 找到输入区域，请手动点击输入框并按 Enter 继续")
                    input("✋ 点击输入框后按 Enter 继续...")
                    return True
                return False

            # 聚焦并输入
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_element)
            time.sleep(1)

            # 先点击输入框确保聚焦
            input_element.click()
            time.sleep(0.5)

            # 清空现有内容
            if input_element.tag_name in ["textarea", "input"]:
                input_element.clear()
            else:
                # contenteditable 元素
                if sys.platform == 'darwin':
                    input_element.send_keys(Keys.COMMAND, 'a')
                else:
                    input_element.send_keys(Keys.CONTROL, 'a')

            # 输入 "/" 命令
            print("⌨️  输入 '/' 命令...")
            input_element.send_keys("/")
            time.sleep(3)  # 等待弹出框出现

            # 查找并点击 "深入研究" 选项
            print("🔍 查找 '深入研究' 选项...")
            research_options = [
                "//div[contains(text(), '深入研究')]",
                "//span[contains(text(), '深入研究')]",
                "//a[contains(text(), '深入研究')]",
                "//button[contains(text(), '深入研究')]",
                "//*[contains(@class, 'command-option') and contains(text(), '深入研究')]"
            ]
            
            research_option_found = False
            for option_xpath in research_options:
                try:
                    options = self.driver.find_elements(By.XPATH, option_xpath)
                    for option in options:
                        if option.is_displayed():
                            self.driver.execute_script("arguments[0].click();", option)
                            print("✅ 选择 '深入研究' 选项")
                            research_option_found = True
                            time.sleep(2)
                            break
                    if research_option_found:
                        break
                except:
                    continue
            
            if not research_option_found:
                print("⚠️  未找到 '深入研究' 选项，直接输入主题")

            # 选择选项后，输入框可能被重新渲染，需要重新查找
            print("🔍 重新查找输入框...")
            input_element = None
            for strategy in input_strategies:
                try:
                    elements = self.driver.find_elements(By.XPATH, strategy)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            input_element = elem
                            print("✅ 重新找到输入框")
                            break
                    if input_element:
                        break
                except:
                    continue
            
            if not input_element:
                print("❌ 重新查找输入框失败")
                return False

            # 确保重新聚焦输入框
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_element)
            time.sleep(0.5)
            input_element.click()
            time.sleep(0.5)
            
            # 再次清空输入框，确保输入主题前内容为空
            print("🗑️  清空输入框内容...")
            if input_element.tag_name in ["textarea", "input"]:
                input_element.clear()
            else:
                # contenteditable 元素
                if sys.platform == 'darwin':
                    input_element.send_keys(Keys.COMMAND, 'a')
                    input_element.send_keys(Keys.DELETE)
                else:
                    input_element.send_keys(Keys.CONTROL, 'a')
                    input_element.send_keys(Keys.DELETE)

            # 输入研究主题
            print("⌨️  输入研究主题...")
            input_element.send_keys(topic)

            print(f"✅ 成功输入主题（长度: {len(topic)} 字符）")
            time.sleep(2)
            return True

        except Exception as e:
            print(f"❌ 输入主题失败: {str(e)}")
            return False

    def wait_and_click_start_research(self):
        """等待并点击开始研究按钮"""
        try:
            print("\n🔍 等待开始研究按钮出现...")
            
            # 开始研究按钮定位策略
            start_research_strategies = [
                "//button[contains(text(), '直接开始研究')]",
                "//button[contains(text(), '立即开始研究')]",
                "//span[contains(text(), '直接开始研究')]",
                "//div[contains(text(), '直接开始研究')]",
                "//button[contains(text(), '开始研究')]",
                "//span[contains(text(), '开始研究')]",
                "//div[contains(text(), '开始研究')]",
                "//button[contains(@class, 'research') and contains(text(), '开始')]",
                "//button[contains(@class, 'research') and contains(text(), '直接')]",
                "//*[contains(@class, 'start-research')]",
                "//*[contains(@class, 'research-start')]",
                "//button[contains(@class, 'primary') and contains(text(), '研究')]",
                "//button[contains(@class, 'confirm') and contains(text(), '研究')]",
                "//button[contains(@class, 'rounded-full') and contains(text(), '研究')]",
            ]
            
            start_time = time.time()
            max_wait = 60  # 1分钟超时
            start_research_button = None
            
            while time.time() - start_time < max_wait:
                for strategy in start_research_strategies:
                    try:
                        elements = self.driver.find_elements(By.XPATH, strategy)
                        for elem in elements:
                            if elem.is_displayed() and elem.is_enabled():
                                start_research_button = elem
                                print("✅ 找到'开始研究'按钮")
                                break
                        if start_research_button:
                            break
                    except:
                        continue
                
                if start_research_button:
                    break
                    
                print("⌛ 等待开始研究按钮出现...")
                time.sleep(3)
            
            if not start_research_button:
                print("⚠️ 未找到'开始研究'按钮，可能已经自动开始")
                return True
            
            # 点击开始研究按钮
            print("🎯 点击'开始研究'按钮...")
            try:
                ActionChains(self.driver).move_to_element(start_research_button).click().perform()
                print("✅ 成功点击'开始研究'按钮")
            except:
                # JavaScript 点击
                self.driver.execute_script("arguments[0].click();", start_research_button)
                print("✅ 使用 JavaScript 点击'开始研究'按钮成功")
            
            time.sleep(2)  # 等待研究开始
            return True
            
        except Exception as e:
            print(f"⚠️ 处理开始研究按钮时异常: {str(e)}")
            return True  # 这不是致命错误，继续执行

    def send_request(self):
        """发送研究请求"""
        try:
            print("\n📤 准备发送研究请求...")

            # 发送按钮定位策略
            send_strategies = [
                # 基于我们测试发现的圆形发送按钮
                "//button[contains(@class, 'rounded-full') and contains(@class, 'flex')]",  # 圆形按钮
                "//button[contains(@class, 'rounded-full')][.//svg]",  # 带SVG图标的圆形按钮
                "//button[contains(@class, 'shrink-0') and contains(@class, 'items-center')][.//svg]",  # 带图标的按钮
                "//button[contains(@class, 'h-32') and contains(@class, 'w-32')]",  # 固定大小的按钮
                "//button[contains(@class, 'outline-transparent') and contains(@class, 'rounded-full')]",  # 圆形透明按钮

                # 直接文本匹配（备用）
                "//button[contains(text(), '发送')]",
                "//button[contains(text(), '提交')]",
                "//span[contains(text(), '发送')]",
                "//div[contains(text(), '发送')]",

                # 图标按钮（通常是发送图标）
                "//button[contains(@class, 'send')]",
                "//button[contains(@class, 'submit')]",

                # 通用提交按钮
                "//button[@type='submit']",
                "//input[@type='submit']",
            ]

            send_button = None
            for strategy in send_strategies:
                try:
                    elements = self.driver.find_elements(By.XPATH, strategy)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            send_button = elem
                            print(f"✅ 找到发送按钮")
                            break
                    if send_button:
                        break
                except:
                    continue

            # 检查是否有"直接开始研究"按钮
            if not send_button:
                print("🔍 查找'直接开始研究'按钮...")
                research_button_strategies = [
                    "//button[contains(text(), '直接开始研究')]",
                    "//span[contains(text(), '直接开始研究')]",
                    "//div[contains(text(), '直接开始研究')]",
                    "//button[contains(@class, 'research') and contains(text(), '开始')]",
                    "//*[contains(@class, 'start-research')]",
                    "//*[contains(@class, 'research-start')]"
                ]
                
                for strategy in research_button_strategies:
                    try:
                        elements = self.driver.find_elements(By.XPATH, strategy)
                        for elem in elements:
                            if elem.is_displayed() and elem.is_enabled():
                                send_button = elem
                                print("✅ 找到'直接开始研究'按钮")
                                break
                        if send_button:
                            break
                    except:
                        continue
            
            if send_button:
                # 点击发送或开始研究按钮
                try:
                    ActionChains(self.driver).move_to_element(send_button).click().perform()
                    print("🎯 成功点击按钮")
                    time.sleep(1)
                    return True
                except:
                    # JavaScript 点击
                    self.driver.execute_script("arguments[0].click();", send_button)
                    print("🎯 使用 JavaScript 点击成功")
                    return True
            else:
                # 尝试快捷键
                print("⚠️ 未找到发送按钮或开始研究按钮，尝试快捷键...")

                # 尝试 Enter
                active_element = self.driver.switch_to.active_element
                if active_element:
                    active_element.send_keys(Keys.ENTER)
                    time.sleep(1)

                    # 检查是否成功（比如按钮变为禁用状态）
                    print("🎯 使用 Enter 发送")
                    return True

                # 尝试 Ctrl+Enter
                try:
                    ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.ENTER).key_up(Keys.CONTROL).perform()
                    print("🎯 使用 Ctrl+Enter 发送")
                    return True
                except:
                    print("❌ 所有发送方式均失败")
                    return False

        except Exception as e:
            print(f"❌ 发送失败: {str(e)}")
            return False

    def monitor_results(self):
        """监控研究结果生成"""
        try:
            print("\n⏳ 等待研究结果生成...")
            print("🔄 这可能需要几分钟，请耐心等待...")

            # 语音输入按钮检测（研究完成的标志）- 参考test_button_detection.py的检测方式
            send_button_indicators = [
                "//div[@data-testid='asr_btn' and @data-state='inactive']",  # 特定测试ID的按钮
                "//div[@data-testid='asr_btn']",  # 忽略状态的asr按钮
            ]

            # 结果区域检测（仅在研究完成后检查）
            result_indicators = [
                "//div[contains(@class, 'assistant')]",
                "//div[contains(@class, 'bot')]",
                "//div[contains(@class, 'response')]",
                "//div[contains(@class, 'answer')]",
                "//div[contains(@class, 'result')]",
                "//div[contains(@class, 'message') and not(contains(@class, 'user'))]",
            ]

            start_time = time.time()
            max_wait = 7200  # 2小时
            check_interval = 2  # 检查间隔

            # 简化监控流程：只要检测到语音输入按钮出现，就认为研究完成
            print("🔍 等待研究完成...")
            research_finished = False
            while time.time() - start_time < max_wait:
                time.sleep(check_interval)
                elapsed = int(time.time() - start_time)

                # 检查语音输入按钮是否出现
                send_button_present = False
                for send_indicator in send_button_indicators:
                    try:
                        send_elements = self.driver.find_elements(By.XPATH, send_indicator)
                        for send_elem in send_elements:
                            if send_elem.is_displayed():
                                # 对于div类型的按钮，只需要检查显示状态
                                if send_elem.tag_name == 'div' or (send_elem.tag_name == 'button' and send_elem.is_enabled()):
                                    send_button_present = True
                                    break
                        if send_button_present:
                            break
                    except Exception as e:
                        continue

                if send_button_present:
                    print(f"✅ 研究完成（总等待时间: {elapsed}秒）")
                    print("🔍 开始检测结果区域...")
                    research_finished = True
                    break

                # 每30秒输出一次状态，避免日志过多
                if elapsed % 30 == 0:
                    print(f"🔄 研究进行中... ({elapsed}秒)")

            if not research_finished:
                print("\n⚠️ 等待超时，但研究可能仍在进行")
                print("💡 请手动查看页面结果")
                return True

            # 阶段3：检测结果区域（仅在研究完成后）
            print("⏳ 正在检测研究结果...")
            result_check_start = time.time()
            result_max_wait = 60  # 1分钟检测结果

            while time.time() - result_check_start < result_max_wait:
                time.sleep(2)

                for indicator in result_indicators:
                    try:
                        elements = self.driver.find_elements(By.XPATH, indicator)
                        for elem in elements:
                            if elem.is_displayed():
                                text = elem.text.strip()
                                if text and len(text) > 10:  # 有实际内容
                                    print("\n✅ 检测到研究结果")
                                    print("-" * 50)
                                    print(text[:200] + "..." if len(text) > 200 else text)
                                    print("-" * 50)
                                    
                                    # 尝试下载Markdown格式的结果
                                    try:
                                        print("📥 尝试下载Markdown格式结果...")
                                        
                                        # 1. 先点击卡片以显示侧边栏
                                        card_indicators = [
                                            "//div[@data-testid='doc_card']",
                                            "//div[@class='card-QqKfCx flow-product-card']",
                                            "//div[contains(@class, 'card-tVgn4t')]",
                                        ]
                                        
                                        card_element = None
                                        for card_indicator in card_indicators:
                                            try:
                                                card_elements = self.driver.find_elements(By.XPATH, card_indicator)
                                                for card_elem in card_elements:
                                                    if card_elem.is_displayed() and card_elem.is_enabled():
                                                        card_element = card_elem
                                                        print("✅ 找到研究结果卡片")
                                                        break
                                                if card_element:
                                                    break
                                            except Exception as e:
                                                continue
                                        
                                        if card_element:
                                            # 点击卡片
                                            self.driver.execute_script("arguments[0].click();", card_element)
                                            print("🔘 点击研究结果卡片")
                                            time.sleep(10)  # 等待侧边栏完全加载
                                        else:
                                            print("⚠️ 未找到研究结果卡片，尝试直接查找下载按钮")
                                        
                                        # 2. 点击下载按钮
                                        download_indicators = [
                                            "//button[contains(text(), '下载')]",
                                            "//div[contains(text(), '下载')]",
                                            "//span[contains(text(), '下载')]",
                                            "//button[contains(@class, 'download')]",
                                            "//*[contains(@class, 'download') and contains(text(), '下载')]",
                                        ]
                                        
                                        download_button = None
                                        for download_indicator in download_indicators:
                                            try:
                                                download_elements = self.driver.find_elements(By.XPATH, download_indicator)
                                                for download_elem in download_elements:
                                                    if download_elem.is_displayed() and download_elem.is_enabled():
                                                        download_button = download_elem
                                                        print("✅ 找到下载按钮")
                                                        break
                                                if download_button:
                                                    break
                                            except Exception as e:
                                                continue
                                        
                                        if download_button:
                                            # 点击下载按钮
                                            self.driver.execute_script("arguments[0].click();", download_button)
                                            print("🔘 点击下载按钮")
                                            time.sleep(2)  # 等待弹出选择菜单
                                            
                                            # 选择Markdown格式
                                            markdown_indicators = [
                                                "//div[@data-testid='popover_select_option_item' and @data-value='markdown']",
                                                "//div[@data-value='markdown']",
                                                "//div[.//div[text()='Markdown']]",
                                                "//div[text()='Markdown']/ancestor::div[1]",
                                                "//div[text()='Markdown']/ancestor::div[2]",
                                                "//div[text()='Markdown']",
                                                "//*[text()='Markdown']",
                                            ]
                                            
                                            markdown_option = None
                                            for markdown_indicator in markdown_indicators:
                                                try:
                                                    markdown_elements = self.driver.find_elements(By.XPATH, markdown_indicator)
                                                    for markdown_elem in markdown_elements:
                                                        if markdown_elem.is_displayed():
                                                            # 检查元素是否可交互
                                                            try:
                                                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", markdown_elem)
                                                                self.driver.execute_script("arguments[0].click();", markdown_elem)
                                                                print("✅ 找到并点击了Markdown格式选项")
                                                                markdown_option = markdown_elem
                                                                break
                                                            except:
                                                                continue
                                                    if markdown_option:
                                                        break
                                                except Exception as e:
                                                    print(f"🔍 尝试选择器 {markdown_indicator} 时出错: {str(e)}")
                                                    continue
                                            
                                            if markdown_option:
                                                print("🔘 选择Markdown格式")
                                                
                                                # 等待下载完成
                                                time.sleep(10)
                                                
                                                # 从Downloads目录拷贝到workspace
                                                try:
                                                    downloads_dir = "C:\\Users\\GYL\\Downloads"
                                                    
                                                    # 获取最新下载的文件
                                                    files = [os.path.join(downloads_dir, f) for f in os.listdir(downloads_dir) 
                                                             if os.path.isfile(os.path.join(downloads_dir, f))]
                                                    if not files:
                                                        print("⚠️ Downloads目录中没有文件")
                                                        return True
                                                    
                                                    # 按修改时间排序，获取最新的文件
                                                    latest_file = max(files, key=os.path.getmtime)
                                                    
                                                    # 生成目标文件名
                                                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                                                    target_file_name = f"research_result_{timestamp}.md"
                                                    target_path = os.path.join(self.workspace_dir, target_file_name)
                                                    
                                                    # 拷贝文件
                                                    shutil.copy2(latest_file, target_path)
                                                    print(f"📁 文件已从Downloads拷贝到: {target_path}")
                                                    print(f"📄 原始文件位置: {latest_file}")
                                                except Exception as copy_e:
                                                    print(f"⚠️ 拷贝文件失败: {str(copy_e)}")
                                            else:
                                                print("⚠️ 未找到Markdown格式选项")
                                        else:
                                            print("⚠️ 未找到下载按钮")
                                    except Exception as download_e:
                                        print(f"⚠️ 下载过程失败: {str(download_e)}")
                                    
                                    return True
                    except:
                        continue

            print("\n⚠️ 结果检测超时")
            print("💡 研究已完成，请手动查看页面结果")

        except Exception as e:
            print(f"⚠️ 等待结果时异常: {str(e)}")
            return True

    def run(self):
        """运行完整流程"""
        success = False

        try:
            print("\n" + "=" * 60)
            print("🤖 豆包深度研究自动化 v2.0")
            print("=" * 60)

            # 1. 访问页面
            if not self.visit_page():
                return False

            # 2. 处理登录
            if not self.check_and_handle_login():
                return False

            # 3. 跳过直接点击研究功能，改用输入框的"/"命令来选择

            # 4. 输入主题
            if not self.input_topic():
                return False

            # 5. 发送请求
            if not self.send_request():
                return False

            # 6. 等待并点击开始研究按钮
            self.wait_and_click_start_research()

            # 7. 监控结果
            self.monitor_results()

            print("\n" + "=" * 60)
            print("🎉 自动化流程完成！")
            print("📊 请查看页面研究结果")
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
            if success:
                print("\n🔚 任务完成！")
            else:
                print("\n💔 任务失败！")
            print("🌐 浏览器保持打开")
        except:
            pass

if __name__ == "__main__":
    # 创建实例并运行
    doubao = DoubaoResearchAuto()
    success = doubao.run()

    # 任务完成后保持程序运行，等待用户按键
    print("\n📌 按任意键退出程序...")
    try:
        # 使用 input() 等待用户按键
        input()
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")

    if not success:
        sys.exit(1)