"""
地理位置与时区工具
基于 IP 地址获取地理位置和当地时间
"""

import httpx
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, Tuple, Optional
from fastapi import Request

async def get_client_ip(request: Request) -> str:
    """
    获取客户端 IP：
    - 先看 X-Forwarded-For（如果有反向代理 / 网关）
    - 再退回到 request.client.host
    """
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # 可能是 "client_ip, proxy1, proxy2" 这种形式，取最左边的
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "127.0.0.1"
    return ip

async def ip_to_location(ip: str) -> Dict[str, Any]:
    """
    调用 ip-api 查询地理位置信息：
    文档: http://ip-api.com/docs/api:json
    注意：免费版不支持 HTTPS，且有速率限制（45次/分）
    """
    # 本地回环地址特殊处理
    if ip in ["127.0.0.1", "localhost", "::1"]:
        return {
            "ip": ip,
            "country": "Local",
            "region": "Local",
            "city": "Local",
            "timezone": "Asia/Shanghai", # 默认给个时区方便测试
            "status": "success"
        }

    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,timezone,query"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            data = resp.json()

        if data.get("status") != "success":
            # 查询失败时返回默认值，避免阻断流程
            return {
                "ip": ip,
                "status": "fail", 
                "message": data.get("message"),
                "timezone": "UTC" # 默认 UTC
            }

        return {
            "ip": data.get("query"),
            "country": data.get("country"),
            "region": data.get("regionName"),
            "city": data.get("city"),
            "timezone": data.get("timezone"),
            "status": "success"
        }
    except Exception as e:
        return {
            "ip": ip,
            "status": "error",
            "message": str(e),
            "timezone": "UTC"
        }

def get_local_time_and_utc_offset(timezone_str: Optional[str] = None) -> Tuple[datetime, str]:
    """
    根据时区字符串（如 'Asia/Tokyo'）计算当前当地时间和 UTC 偏移。
    如果 timezone_str 为空或无效，默认使用 UTC。
    """
    try:
        tz = ZoneInfo(timezone_str) if timezone_str else ZoneInfo("UTC")
    except Exception:
        tz = ZoneInfo("UTC")
        
    now_local = datetime.now(tz)

    # 计算相对于 UTC 的偏移
    offset = now_local.utcoffset()
    # offset 可能是 None，一般不会，这里防个空
    if offset is None:
        offset_hours = 0
        offset_minutes = 0
    else:
        total_minutes = int(offset.total_seconds() // 60)
        offset_hours = total_minutes // 60
        offset_minutes = abs(total_minutes % 60)

    sign = "+" if offset_hours >= 0 else "-"
    # 注意小时要取绝对值防止出现 "--"
    offset_str = f"UTC{sign}{abs(offset_hours):02d}:{offset_minutes:02d}"

    return now_local, offset_str
