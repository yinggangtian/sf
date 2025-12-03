#!/usr/bin/env python3
"""
API 接口测试工具
测试 /v1/responses 接口 (OpenAI Responses API 格式)

使用方法:
    1. 确保后端服务已启动 (uv run fastapi dev app/main.py)
    2. 运行测试: uv run python scripts/test_api.py [测试语句]
"""

import asyncio
import httpx
import json
import sys
from typing import List, Dict, Any

API_URL = "http://localhost:8000/v1/responses"

async def test_response_api(query: str):
    print(f"🔌 连接到: {API_URL}")
    print(f"📝 发送请求: {query}")
    print("-" * 60)

    # 构造符合 ResponseRequest 定义的请求体
    # 对应 app/routes/ai.py 中的 ResponseRequest
    payload = {
        "model": "liuren-master",
        "input": query,  # 支持直接传字符串
        "user_id": 1,
        "session_id": "test_session_001"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(API_URL, json=payload, timeout=60.0)
            
            if response.status_code != 200:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                try:
                    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
                except:
                    print(response.text)
                return

            data = response.json()
            
            print("\n📊 响应结果:")
            print("=" * 60)
            
            # 解析并打印输出
            # 对应 app/routes/ai.py 中的 ResponseOutput -> OutputMessage
            if "output" in data:
                for item in data["output"]:
                    if item.get("type") == "message" and "content" in item:
                        for content_part in item["content"]:
                            if content_part.get("type") == "text":
                                print(content_part.get("text", ""))
            
            print("\n" + "=" * 60)
            
            # 打印元数据和占卜结果
            if "divination_result" in data and data["divination_result"]:
                print("\n🔮 占卜结果数据:")
                print(json.dumps(data["divination_result"], indent=2, ensure_ascii=False))
            
            if "metadata" in data and data["metadata"]:
                print("\nℹ️ 元数据:")
                print(json.dumps(data["metadata"], indent=2, ensure_ascii=False))
            
            if "usage" in data:
                print(f"\n📊 Token 使用: {data['usage']}")

            print("\n✅ 测试完成")

    except httpx.RequestError as e:
        print(f"\n❌ 连接错误: {str(e)}")
        print("请确保后端服务已启动 (默认 http://localhost:8000)")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")

def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "8, 6, 男, 想问一下我明年爱情怎么样"
    
    asyncio.run(test_response_api(query))

if __name__ == "__main__":
    main()
