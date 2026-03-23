#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests>=2.28.0",
# ]
# ///
"""
测试脚本 - 验证视频创作软件 API 是否正常工作

Usage:
    uv run test_all.py [--account 账号 --password 密码] [--url "测试用抖音链接"] [--full]

测试流程:
    1. ping 健康检查
    2. login 登录（如果提供了账号密码）
    3. extract_text 提取文案（如果提供了 url）
    4. rewrite_text 改写文案
    5-12. (--full 模式) generate_voice → generate_video → create_subtitle → add_subtitle → add_bgm → generate_cover → generate_title_tags → publish
"""

import argparse
import sys
import time

import requests

API_BASE = "http://127.0.0.1:18900"
POLL_INTERVAL = 3
POLL_TIMEOUT = 300


def api_get(path: str) -> dict | None:
    try:
        resp = requests.get(f"{API_BASE}{path}", timeout=10)
        return resp.json()
    except requests.ConnectionError:
        return None
    except Exception as e:
        print(f"  请求异常: {e}")
        return None


def api_post(path: str, data: dict) -> dict | None:
    try:
        resp = requests.post(f"{API_BASE}{path}", json=data, timeout=10)
        return resp.json()
    except requests.ConnectionError:
        return None
    except Exception as e:
        print(f"  请求异常: {e}")
        return None


def poll_task(task_id: str) -> dict | None:
    start = time.time()
    last_msg = ""
    while time.time() - start < POLL_TIMEOUT:
        result = api_get(f"/api/task/{task_id}")
        if not result:
            return None

        msg = result.get("message", "")
        if msg and msg != last_msg:
            print(f"  进度: {msg}")
            last_msg = msg

        status = result.get("status")
        if status in ("success", "failed"):
            return result

        time.sleep(POLL_INTERVAL)

    print("  超时!")
    return None


def test_ping():
    print("=" * 50)
    print("[测试 1] Ping 健康检查")
    print("=" * 50)
    result = api_get("/api/ping")
    if result and result.get("status") == "ok":
        logged_in = result.get("is_logged_in", False)
        status_text = "已登录" if logged_in else "未登录"
        print(f"  ✅ 通过: {result.get('message')} ({status_text})")
        return True, logged_in
    else:
        print("  ❌ 失败: 无法连接到软件 API")
        return False, False


def test_login(account: str, password: str):
    print()
    print("=" * 50)
    print("[测试 2] 登录")
    print("=" * 50)
    print(f"  账号: {account}")

    result = api_post("/api/login", {"account": account, "password": password})
    if not result:
        print("  ❌ 失败: 无法提交登录请求")
        return False

    if result.get("status") == "ok":
        print(f"  ✅ 通过: {result.get('message', '已登录')}")
        return True

    if "error" in result:
        print(f"  ❌ 失败: {result['error']}")
        return False

    task_id = result.get("task_id")
    if not task_id:
        print("  ❌ 失败: 未获取到任务ID")
        return False

    print(f"  任务ID: {task_id}")
    task_result = poll_task(task_id)
    if not task_result:
        print("  ❌ 失败: 登录任务异常")
        return False

    if task_result["status"] == "success":
        print(f"  ✅ 通过: {task_result.get('message')}")
        return True
    else:
        print(f"  ❌ 失败: {task_result.get('message')}")
        return False


def test_extract_text(url: str):
    print()
    print("=" * 50)
    print("[测试 3] 提取文案")
    print("=" * 50)
    print(f"  URL: {url}")

    result = api_post("/api/extract_text", {"url": url, "url_type": "抖音分享链接"})
    if not result:
        print("  ❌ 失败: 无法提交任务")
        return None

    if "error" in result:
        print(f"  ❌ 失败: {result['error']}")
        return None

    task_id = result["task_id"]
    print(f"  任务ID: {task_id}")

    task_result = poll_task(task_id)
    if not task_result:
        print("  ❌ 失败: 任务执行异常")
        return None

    if task_result["status"] == "success":
        text = task_result.get("result", {}).get("text", "")
        print(f"  ✅ 通过: 提取到 {len(text)} 字")
        print(f"  文案预览: {text[:100]}...")
        return text
    else:
        print(f"  ❌ 失败: {task_result.get('message')}")
        return None


def test_rewrite_text(text: str):
    print()
    print("=" * 50)
    print("[测试 4] 改写文案")
    print("=" * 50)
    print(f"  原文预览: {text[:80]}...")

    result = api_post("/api/rewrite_text", {
        "text": text,
        "mode": "自动仿写",
        "prompt": "",
    })
    if not result:
        print("  ❌ 失败: 无法提交任务")
        return False

    if "error" in result:
        print(f"  ❌ 失败: {result['error']}")
        return False

    task_id = result.get("task_id")
    if not task_id:
        print("  ❌ 失败: 未获取到任务ID")
        return False

    print(f"  任务ID: {task_id}")

    task_result = poll_task(task_id)
    if not task_result:
        print("  ❌ 失败: 任务执行异常")
        return False

    if task_result["status"] == "success":
        rewritten = task_result.get("result", {}).get("text", "")
        print(f"  ✅ 通过: 改写后 {len(rewritten)} 字")
        print(f"  改写预览: {rewritten[:100]}...")
        return True
    else:
        print(f"  ❌ 失败: {task_result.get('message')}")
        return False


def test_simple_trigger(test_num: int, action: str, label: str):
    """通用的简单触发测试"""
    print()
    print("=" * 50)
    print(f"[测试 {test_num}] {label}")
    print("=" * 50)

    result = api_post(f"/api/{action}", {})
    if not result:
        print("  ❌ 失败: 无法提交任务")
        return False

    if "error" in result:
        print(f"  ❌ 失败: {result['error']}")
        return False

    task_id = result.get("task_id")
    if not task_id:
        print("  ❌ 失败: 未获取到任务ID")
        return False

    print(f"  任务ID: {task_id}")

    task_result = poll_task(task_id)
    if not task_result:
        print("  ❌ 失败: 任务执行异常")
        return False

    if task_result["status"] == "success":
        msg = task_result.get("message", "")
        print(f"  ✅ 通过: {msg}")
        return True
    else:
        print(f"  ❌ 失败: {task_result.get('message')}")
        return False


def main():
    parser = argparse.ArgumentParser(description="视频创作软件 API 测试")
    parser.add_argument("--account", help="登录账号")
    parser.add_argument("--password", help="登录密码")
    parser.add_argument("--url", help="测试用抖音分享链接")
    parser.add_argument("--full", action="store_true", help="执行完整流程测试（包括语音、视频、字幕等）")
    args = parser.parse_args()

    print("🧪 开始测试视频创作软件 API")
    print()

    # 测试 1: Ping
    ping_ok, is_logged_in = test_ping()
    if not ping_ok:
        print("\n❌ 软件未启动或 API 服务未运行，测试终止")
        sys.exit(1)

    # 测试 2: 登录
    if not is_logged_in:
        if args.account and args.password:
            if not test_login(args.account, args.password):
                print("\n❌ 登录失败，测试终止")
                sys.exit(1)
        else:
            print("\n⏭️  跳过登录测试（未提供 --account --password，且软件未登录）")
            print("   后续需要登录的接口将无法测试")

    # 测试 3: 提取文案
    extracted_text = None
    if args.url:
        extracted_text = test_extract_text(args.url)
    else:
        print("\n⏭️  跳过提取文案测试（未提供 --url 参数）")

    # 测试 4: 改写文案
    test_text = extracted_text or "今天天气真好，阳光明媚，适合出去散步。生活中总有一些美好的瞬间值得我们去记录和分享。"
    test_rewrite_text(test_text)

    # 测试 5-12: 完整流程（需要 --full 参数）
    if args.full:
        full_steps = [
            (5, "generate_voice", "生成语音"),
            (6, "generate_video", "生成数字人视频"),
            (7, "create_subtitle", "生成字幕"),
            (8, "add_subtitle", "添加字幕到视频"),
            (9, "add_bgm", "添加背景音乐"),
            (10, "generate_cover", "生成封面"),
            (11, "generate_title_tags", "生成标题标签"),
            (12, "publish", "一键发布"),
        ]
        for num, action, label in full_steps:
            if not test_simple_trigger(num, action, label):
                print(f"\n⚠️  {label} 失败，后续步骤可能受影响")
    else:
        print("\n⏭️  跳过完整流程测试（添加 --full 参数启用）")

    print()
    print("=" * 50)
    print("🧪 测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
