"""
智能搜索服务 - 为Fintech2026提供网络搜索功能
使用百度搜索API（无需密钥）
"""

import requests
from datetime import datetime
import re


class SearchService:
    """搜索服务类 - 提供网络搜索功能"""
    
    def __init__(self):
        print(f"✅ 智能搜索服务初始化成功")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def search_baidu(self, query, num_results=5):
        """使用百度搜索"""
        try:
            # 使用百度搜索
            search_url = f"https://www.baidu.com/s?wd={query}&rn={num_results}"
            
            response = requests.get(
                search_url,
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                # 简单提取搜索结果标题
                content = response.text
                # 提取标题（简化版）
                titles = re.findall(r'<h3[^>]*>(.*?)</h3>', content)
                
                results = []
                for i, title in enumerate(titles[:num_results]):
                    # 清理HTML标签
                    clean_title = re.sub(r'<[^>]+>', '', title)
                    results.append({
                        'title': clean_title,
                        'url': f'https://www.baidu.com/s?wd={query}'
                    })
                
                return results
            else:
                return []
                
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def search_fintech_info(self, query):
        """
        搜索Fintech2026相关信息
        返回预设的常见问题答案
        """
        # 预设的常见问题答案
        faq = {
            '消费记录': {
                'answer': '您可以在主页向下滚动查看"消费记录"部分，那里会显示您的所有交易记录。',
                'keywords': ['消费', '记录', '交易', '流水', '账单']
            },
            '信用额度': {
                'answer': '您的信用额度显示在主页的信用卡上。额度是根据您上传的银行流水和余额证明通过AI模型预测得出的。',
                'keywords': ['额度', '信用', '授信', '限额']
            },
            '盲盒抽奖': {
                'answer': '在主页下方有"盲盒抽奖"功能，消耗WECoin可以抽取各种奖品。点击"翻牌"按钮即可参与。',
                'keywords': ['盲盒', '抽奖', '翻牌', '奖品', 'wecoin']
            },
            'WECoin': {
                'answer': 'WECoin是系统的虚拟货币，可以通过消费获得，用于参与盲盒抽奖等活动。您的WECoin余额显示在主页顶部。',
                'keywords': ['wecoin', '积分', '货币', '余额']
            },
            '修改信息': {
                'answer': '点击主页右上角的设置图标（齿轮），可以修改用户名、密码，或退出登录。',
                'keywords': ['修改', '设置', '用户名', '密码', '退出']
            },
            '注册': {
                'answer': '注册需要上传护照、入关小票、银行流水、余额证明等文件，并录入Face ID。完成后系统会自动评估您的信用额度。',
                'keywords': ['注册', '开户', '申请', '办理']
            }
        }
        
        # 查找匹配的问题
        query_lower = query.lower()
        for topic, info in faq.items():
            for keyword in info['keywords']:
                if keyword in query_lower:
                    return {
                        'success': True,
                        'response': info['answer'],
                        'source': 'Fintech2026 FAQ',
                        'search_results': [],
                        'timestamp': datetime.now().isoformat()
                    }
        
        # 如果没有匹配，进行网络搜索
        search_results = self.search_baidu(query)

        if search_results:
            response_text = f"关于「{query}」的搜索结果如下，请查看参考资料。"
        else:
            response_text = f"抱歉，暂时无法找到关于「{query}」的相关信息。\n\n您可以尝试：\n1. 查看主页的消费记录\n2. 点击右上角设置按钮\n3. 查看信用卡上的额度信息"
        
        return {
            'success': True,
            'response': response_text,
            'source': 'Web Search',
            'search_results': search_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def check_service_status(self):
        """检查服务状态"""
        return {
            'available': True,
            'service': 'Search Service',
            'version': '1.0'
        }

