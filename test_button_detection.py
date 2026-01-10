import time
import config
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Try to import webdriver-manager, will use if available
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

class ButtonDetectionTest:
    def __init__(self, use_webdriver_manager=True):
        # 导入配置
        self.config = config
        
        # 确保目录存在
        self.config.ensure_dirs()
        
        # 设置webdriver
        self.setup_driver(use_webdriver_manager)
        
    def setup_driver(self, use_webdriver_manager):
        """设置Chrome驱动，与doubao_research_auto保持一致"""
        chrome_options = Options()
        # 反检测选项
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 使用配置的Chrome用户数据目录
        chrome_options.add_argument(f"--user-data-dir={self.config.CHROME_PROFILE_DIR}")
        
        # 其他选项
        chrome_options.add_argument("--start-maximized")
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
        
    def test_button_detection(self):
        try:
            # 使用config中的豆包网址配置
            test_url = self.config.DOUBAO_URL
            print(f"正在打开测试页面: {test_url}")
            self.driver.get(test_url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 测试语音输入按钮检测
            print("\n=== 开始测试语音输入按钮检测 ===")
            
            # 各种可能的按钮检测规则
            button_rules = [
                "//div[@data-testid='asr_btn' and @data-state='inactive']",
                "//div[@data-testid='asr_btn']",
                "//div[contains(@class, 'container-PEnDS2') and contains(@class, 'rounded-full')]",
                "//div[@data-trigger-type='hover']",
                "//div[contains(@class, 'bg-dbx-fill-trans-20') and contains(@class, 'cursor-pointer')]",
                "//div[contains(@class, 'size-36') and contains(@class, 'rounded-full')]",
                "//div[.//svg[@width='24' and @height='24']]",
            ]
            
            for i, rule in enumerate(button_rules):
                print(f"\n测试规则 {i+1}: {rule}")
                try:
                    elements = self.driver.find_elements(By.XPATH, rule)
                    print(f"  找到元素数量: {len(elements)}")
                    
                    for j, elem in enumerate(elements):
                        if elem.is_displayed():
                            print(f"  元素 {j+1}: 可见")
                            print(f"    标签名: {elem.tag_name}")
                            print(f"    文本内容: '{elem.text.strip()}'")
                            print(f"    class: {elem.get_attribute('class')}")
                            print(f"    data-testid: {elem.get_attribute('data-testid')}")
                            print(f"    data-state: {elem.get_attribute('data-state')}")
                            print(f"    data-trigger-type: {elem.get_attribute('data-trigger-type')}")
                            print(f"    is_enabled: {elem.is_enabled() if elem.tag_name == 'button' else 'N/A (div元素)'}")
                        else:
                            print(f"  元素 {j+1}: 不可见")
                except Exception as e:
                    print(f"  检测失败: {str(e)}")
            
            # 手动检查页面结构
            print("\n=== 页面结构检查 ===")
            print("按Enter键保存页面HTML到文件，然后关闭浏览器...")
            input()
            
            # 保存页面HTML
            with open("page_html.txt", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print("页面HTML已保存到 page_html.txt")
            
        except Exception as e:
            print(f"测试过程中出错: {str(e)}")
        finally:
            self.driver.quit()

if __name__ == "__main__":
    test = ButtonDetectionTest()
    test.test_button_detection()