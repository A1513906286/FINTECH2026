"""
阿布扎比推荐服务 - 使用Ollama和DuckDuckGo自动生成推荐
改编自 networked_chat.py
使用DuckDuckGo HTML搜索接口
"""

import requests
from datetime import datetime
import random
import json
from bs4 import BeautifulSoup
import re


class AbuDhabiService:
    def __init__(self, model_name="llama3.2:3b", use_proxy=True, proxy_url="http://127.0.0.1:7890", ollama_url="http://127.0.0.1:11434"):
        """
        初始化阿布扎比推荐服务

        参数:
            model_name: Ollama模型名称
            use_proxy: 是否使用代理（默认True）
            proxy_url: 代理地址（默认Clash代理端口7890）
            ollama_url: Ollama服务地址
        """
        self.model_name = model_name
        self.use_proxy = use_proxy
        self.ollama_url = ollama_url

        # 配置代理
        if use_proxy:
            self.proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            print(f"🌐 已启用代理: {proxy_url}")
        else:
            self.proxies = None
            print("🌐 未使用代理")

        # 测试 Ollama 连接
        try:
            test_url = f"{ollama_url}/api/tags"
            response = requests.get(test_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ Ollama服务连接成功，模型: {model_name}")
            else:
                print(f"⚠️ Ollama服务响应异常: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Ollama服务连接失败: {e}")
            print("💡 提示: 请确保Ollama已安装并运行 (ollama serve)")
    
    def translate_to_english(self, chinese_query):
        """
        将中文查询翻译成英文（使用预定义映射）
        DuckDuckGo API 对英文查询支持更好
        """
        translation_map = {
            "阿布扎比必去景点": "Abu Dhabi top attractions",
            "阿布扎比美食推荐": "Abu Dhabi best restaurants",
            "阿布扎比购物中心": "Abu Dhabi shopping malls",
            "阿布扎比文化体验": "Abu Dhabi cultural experiences",
            "阿布扎比海滩度假": "Abu Dhabi beach resorts",
            "阿布扎比": "Abu Dhabi"
        }

        # 查找最佳匹配
        for cn_key, en_value in translation_map.items():
            if cn_key in chinese_query:
                return en_value

        # 如果没有匹配，返回 "Abu Dhabi" + 原查询
        return f"Abu Dhabi {chinese_query}"

    def search_duckduckgo(self, query, num_results=3, timeout=10):
        """
        使用DuckDuckGo HTML搜索接口进行搜索（支持代理）
        自动将中文查询翻译成英文以提高搜索成功率
        """
        try:
            # 检测是否为中文查询，如果是则翻译成英文
            original_query = query
            if any('\u4e00' <= char <= '\u9fff' for char in query):
                query = self.translate_to_english(query)
                print(f"🌐 翻译查询: {original_query} -> {query}")

            # 使用DuckDuckGo HTML搜索接口
            url = "https://duckduckgo.com/html/"
            params = {
                "q": query
            }

            # 设置请求头，模拟浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            print(f"🔍 正在搜索: {query}")

            # 使用代理（如果已配置）
            response = requests.get(
                url,
                params=params,
                headers=headers,
                proxies=self.proxies,  # 使用代理
                timeout=timeout
            )
            response.raise_for_status()

            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # 查找搜索结果
            # DuckDuckGo HTML版本的搜索结果在 class="result" 的div中
            result_divs = soup.find_all('div', class_='result')

            for result_div in result_divs[:num_results]:
                try:
                    # 提取标题和链接
                    title_tag = result_div.find('a', class_='result__a')
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        # 提取真实URL（DuckDuckGo会重定向）
                        url_link = title_tag.get('href', '')

                        # 清理URL（移除DuckDuckGo的重定向）
                        if url_link.startswith('//duckduckgo.com/l/?'):
                            # 从重定向URL中提取真实URL
                            match = re.search(r'uddg=([^&]+)', url_link)
                            if match:
                                import urllib.parse
                                url_link = urllib.parse.unquote(match.group(1))

                        if title and url_link:
                            results.append({
                                'title': title[:100],
                                'url': url_link
                            })
                except Exception as e:
                    print(f"⚠️ 解析单个结果失败: {e}")
                    continue

                if len(results) >= num_results:
                    break

            # 如果还是没有结果，尝试使用通用的 "Abu Dhabi" 查询
            if not results and original_query != "Abu Dhabi":
                print(f"⚠️ 未找到结果，尝试使用通用查询: Abu Dhabi")
                return self.search_duckduckgo("Abu Dhabi", num_results, timeout)

            if results:
                print(f"✅ 搜索成功: {query} - 找到 {len(results)} 条结果")
            else:
                print(f"⚠️ 搜索未找到结果: {query}")

            return results

        except Exception as e:
            print(f"❌ 搜索失败: {query} - {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def generate_recommendations(self):
        """
        自动生成阿布扎比推荐
        返回3条推荐信息
        """
        
        try:
            # 定义推荐主题
            topics = [
                "阿布扎比必去景点",
                "阿布扎比美食推荐",
                "阿布扎比购物中心",
                "阿布扎比文化体验",
                "阿布扎比海滩度假"
            ]
            
            # 随机选择一个主题
            topic = random.choice(topics)
            
            # 搜索相关信息
            print(f"🔍 正在搜索: {topic}")
            search_results = self.search_duckduckgo(topic, num_results=5)
            
            if not search_results:
                return self._get_default_recommendations()
            
            # 构建提示词
            search_context = "\n".join([
                f"- {r['title']}" for r in search_results[:3]
            ])
            
            system_prompt = """你是阿布扎比旅游专家。请根据搜索结果，生成3条简短的阿布扎比推荐。
每条推荐格式：
1. 标题（10-15字）
2. 简介（20-30字）

要求：
- 简洁有趣
- 适合游客
- 突出特色
- 用中文回答"""

            user_prompt = f"""基于以下搜索结果，生成3条阿布扎比推荐：

{search_context}

请严格按照以下JSON格式输出：
[
  {{"title": "标题1", "description": "简介1"}},
  {{"title": "标题2", "description": "简介2"}},
  {{"title": "标题3", "description": "简介3"}}
]"""

            # 调用Ollama生成推荐（使用原始HTTP请求）
            print("🤖 正在生成推荐...")

            ollama_api_url = f"{self.ollama_url}/api/chat"
            payload = {
                "model": self.model_name,
                "messages": [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                "stream": False,
                "options": {
                    'temperature': 0.7,
                    'num_predict': 500
                }
            }

            response = requests.post(
                ollama_api_url,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            ai_response = data.get('message', {}).get('content', '')
            
            # 解析AI响应
            recommendations = self._parse_ai_response(ai_response, search_results)
            
            print(f"✅ 生成了 {len(recommendations)} 条推荐")
            return recommendations
            
        except Exception as e:
            print(f"❌ 生成推荐失败: {str(e)}")
            print(f"❌ 错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return self._get_default_recommendations()
    
    def _parse_ai_response(self, ai_response, search_results):
        """解析AI响应，提取推荐信息"""
        try:
            import json
            import re
            
            # 尝试提取JSON
            json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
            if json_match:
                recommendations_data = json.loads(json_match.group())
                
                # 组合AI生成的标题和搜索结果的链接
                recommendations = []
                for i, item in enumerate(recommendations_data[:3]):
                    rec = {
                        'title': item.get('title', f'推荐 {i+1}'),
                        'description': item.get('description', ''),
                        'url': search_results[i]['url'] if i < len(search_results) else '#',
                        'icon': self._get_icon_for_index(i)
                    }
                    recommendations.append(rec)
                
                return recommendations
        except:
            pass
        
        # 如果解析失败，使用搜索结果
        return self._format_search_results(search_results)
    
    def _format_search_results(self, search_results):
        """格式化搜索结果为推荐格式"""
        recommendations = []
        for i, result in enumerate(search_results[:3]):
            recommendations.append({
                'title': result['title'][:30],
                'description': '点击查看详情',
                'url': result['url'],
                'icon': self._get_icon_for_index(i)
            })
        return recommendations
    
    def _get_icon_for_index(self, index):
        """根据索引返回图标emoji"""
        icons = ['🏛️', '🏖️', '🍽️', '🛍️', '🎨', '🕌']
        return icons[index % len(icons)]
    
    def _get_default_recommendations(self):
        """返回默认推荐（当Ollama不可用时）"""
        return [
            {
                'title': '阿布扎比8大必游景点盘点',
                'description': '探索阿布扎比最受欢迎的旅游景点',
                'url': 'https://www.mafengwo.cn/gonglve/ziyouxing/267891.html',
                'icon': '🏛️'
            },
            {
                'title': 'Abu Dhabi Mall',
                'description': '阿布扎比最大的购物中心',
                'url': 'https://www.abudhabimall.com',
                'icon': '🛍️'
            },
            {
                'title': '10 大阿布扎比最佳美食餐厅 (2025)',
                'description': '品尝地道的阿联酋美食',
                'url': 'https://www.tripadvisor.cn/Restaurants-g295424-Abu_Dhabi.html',
                'icon': '🍽️'
            }
        ]

