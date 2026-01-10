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
                print("\n请按以下步骤登录：")
                print("1. 在浏览器中扫描二维码或使用手机号登录")
                print("2. 登录成功后页面会自动刷新")
                print("3. 登录完成后，按 Enter 键继续自动化流程")
                print("\n" + "-" * 50)

                # 等待用户登录
                input("✋ 登录完成后请按 Enter 键继续...")

                # 等待页面更新
                print("\n⏳ 确认登录状态...")
                time.sleep(3)

                # 再次检查登录状态
                current_url = self.driver.current_url
                if "doubao.com" in current_url:
                    print("✅ 登录状态确认成功")
                    return True
                else:
                    print("⚠️ 请确认登录成功")
                    return True

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

            # 使用配置中的研究主题
            topic = config.RESEARCH_TOPIC

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

            # 输入研究主题
            print("⌨️  输入研究主题...")
            input_element.send_keys(topic)

            print(f"✅ 成功输入主题（长度: {len(topic)} 字符）")
            time.sleep(2)
            return True

        except Exception as e:
            print(f"❌ 输入主题失败: {str(e)}")
            return False

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

            if send_button:
                # 点击发送
                try:
                    ActionChains(self.driver).move_to_element(send_button).click().perform()
                    print("🎯 成功点击发送")
                    time.sleep(1)
                    return True
                except:
                    # JavaScript 点击
                    self.driver.execute_script("arguments[0].click();", send_button)
                    print("🎯 使用 JavaScript 发送成功")
                    return True
            else:
                # 尝试快捷键
                print("⚠️ 未找到发送按钮，尝试快捷键...")

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

            # 结果区域检测
            result_indicators = [
                "//div[contains(@class, 'assistant')]",
                "//div[contains(@class, 'bot')]",
                "//div[contains(@class, 'response')]",
                "//div[contains(@class, 'answer')]",
                "//div[contains(@class, 'result')]",
                "//div[contains(@class, 'message') and not(contains(@class, 'user'))]",
            ]

            start_time = time.time()
            max_wait = 300  # 5分钟

            while time.time() - start_time < max_wait:
                time.sleep(3)
                elapsed = int(time.time() - start_time)

                for indicator in result_indicators:
                    try:
                        elements = self.driver.find_elements(By.XPATH, indicator)
                        for elem in elements:
                            if elem.is_displayed():
                                text = elem.text.strip()
                                if text and len(text) > 10:  # 有实际内容
                                    print(f"\n✅ 检测到研究结果（等待时间: {elapsed}秒）")
                                    print("-" * 50)
                                    print(text[:200] + "..." if len(text) > 200 else text)
                                    print("-" * 50)
                                    return True
                    except:
                        continue

                print(f"⏳ 等待中... ({elapsed}秒)")

            print("\n⚠️ 等待超时，但研究可能仍在进行")
            print("💡 请手动查看页面结果")
            return True

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

            # 6. 监控结果
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
                print("\n🔚 任务完成！是否关闭浏览器？")
                print("(输入 y 关闭，其他键保持打开)")
            else:
                print("\n💔 任务失败！是否关闭浏览器？")
                print("(输入 y 关闭，其他键保持打开以调试)")

            choice = input("请选择: ").strip().lower()
            if choice == 'y':
                self.driver.quit()
                print("\n👋 浏览器已关闭")
            else:
                print("\n🌐 浏览器保持打开")
        except:
            pass

if __name__ == "__main__":
    # 创建实例并运行
    doubao = DoubaoResearchAuto()
    success = doubao.run()

    if not success:
        sys.exit(1)