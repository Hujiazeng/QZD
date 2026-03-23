#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests>=2.28.0",
# ]
# ///
"""
视频创作软件控制脚本 - 龙虾(openclaw) skill 总入口
 
Usage:
    uv run operate.py --action ping
    uv run operate.py --action login --account "账号" --password "密码"
    uv run operate.py --action extract_text --url "抖音链接"
    uv run operate.py --action rewrite_text --text "文案内容"
    uv run operate.py --action status --task-id "task_id"
"""

import argparse
import sys
import time

import requests

API_BASE = "http://127.0.0.1:18900"
POLL_INTERVAL = 3  # 轮询间隔（秒）
POLL_TIMEOUT = 300  # 最大等待时间（秒）


def api_request(method: str, path: str, json_data: dict = None) -> dict | None:
    """发送 API 请求"""
    url = f"{API_BASE}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, timeout=10)
        else:
            resp = requests.post(url, json=json_data or {}, timeout=10)
        return resp.json()
    except requests.ConnectionError:
        print("ERROR: 无法连接到软件，请确保视频创作软件已启动", file=sys.stderr)
        sys.exit(1)
    except requests.Timeout:
        print("ERROR: 请求超时", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: 请求失败: {e}", file=sys.stderr)
        sys.exit(1)


def poll_task(task_id: str) -> dict:
    """轮询任务状态直到完成"""
    start_time = time.time()
    last_message = ""

    while time.time() - start_time < POLL_TIMEOUT:
        result = api_request("GET", f"/api/task/{task_id}")
        if not result:
            print("ERROR: 查询任务状态失败", file=sys.stderr)
            sys.exit(1)

        status = result.get("status", "")
        message = result.get("message", "")

        if message and message != last_message:
            print(f"PROGRESS: {message}")
            last_message = message

        if status == "success":
            return result
        elif status == "failed":
            print(f"ERROR: {message}", file=sys.stderr)
            sys.exit(1)

        time.sleep(POLL_INTERVAL)

    print("ERROR: 任务超时，请稍后重试", file=sys.stderr)
    sys.exit(1)


def action_ping():
    """健康检查"""
    result = api_request("GET", "/api/ping")
    if result and result.get("status") == "ok":
        logged_in = result.get("is_logged_in", False)
        status_text = "已登录" if logged_in else "未登录"
        print(f"SUCCESS: {result.get('message', '服务运行中')} ({status_text})")
    else:
        print("ERROR: 服务异常", file=sys.stderr)
        sys.exit(1)


def action_login(account: str, password: str):
    """登录"""
    if not account or not password:
        print("ERROR: --account 和 --password 参数不能为空", file=sys.stderr)
        sys.exit(1)

    print("PROGRESS: 正在提交登录请求...")
    result = api_request("POST", "/api/login", {
        "account": account,
        "password": password,
    })

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    # 如果已经登录
    if result.get("status") == "ok":
        print(f"SUCCESS: {result.get('message', '已登录')}")
        return

    task_id = result["task_id"]
    print(f"PROGRESS: 登录任务已提交 (task_id: {task_id})...")

    task_result = poll_task(task_id)
    print(f"SUCCESS: {task_result.get('message', '登录成功')}")


def action_extract_text(url: str, url_type: str):
    """提取文案"""
    if not url:
        print("ERROR: --url 参数不能为空", file=sys.stderr)
        sys.exit(1)

    print("PROGRESS: 正在提交提取文案任务...")
    result = api_request("POST", "/api/extract_text", {
        "url": url,
        "url_type": url_type,
    })

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    task_id = result["task_id"]
    print(f"PROGRESS: 任务已提交 (task_id: {task_id})，等待执行...")

    task_result = poll_task(task_id)
    text = task_result.get("result", {}).get("text", "")

    print("SUCCESS: 文案提取完成")
    print("---TEXT_START---")
    print(text)
    print("---TEXT_END---")


def action_rewrite_text(text: str, mode: str, prompt: str):
    """改写文案"""
    if not text:
        print("ERROR: --text 参数不能为空", file=sys.stderr)
        sys.exit(1)

    print("PROGRESS: 正在提交改写文案任务...")
    result = api_request("POST", "/api/rewrite_text", {
        "text": text,
        "mode": mode,
        "prompt": prompt,
    })

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    task_id = result["task_id"]
    print(f"PROGRESS: 任务已提交 (task_id: {task_id})，等待执行...")

    task_result = poll_task(task_id)
    rewritten = task_result.get("result", {}).get("text", "")

    print("SUCCESS: 文案改写完成")
    print("---TEXT_START---")
    print(rewritten)
    print("---TEXT_END---")


def action_simple_trigger(action: str, api_path: str, body: dict = None):
    """通用的简单触发操作：提交 → 轮询 → 返回结果"""
    print(f"PROGRESS: 正在提交 {action} 任务...")
    result = api_request("POST", api_path, body or {})

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    task_id = result["task_id"]
    print(f"PROGRESS: 任务已提交 (task_id: {task_id})，等待执行...")

    task_result = poll_task(task_id)
    message = task_result.get("message", "")
    print(f"SUCCESS: {action} 完成 - {message}")

    # 如果结果中有文本或路径，输出
    res = task_result.get("result", {})
    if res:
        for key in ("text", "audio_path", "video_path", "image_path", "subtitle"):
            val = res.get(key, "")
            if val:
                print(f"RESULT_{key.upper()}: {val}")


def action_status(task_id: str):
    """查询任务状态"""
    if not task_id:
        print("ERROR: --task-id 参数不能为空", file=sys.stderr)
        sys.exit(1)

    result = api_request("GET", f"/api/task/{task_id}")
    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    status = result.get("status", "unknown")
    message = result.get("message", "")
    print(f"STATUS: {status}")
    if message:
        print(f"MESSAGE: {message}")
    if result.get("result"):
        text = result["result"].get("text", "")
        if text:
            print("---TEXT_START---")
            print(text)
            print("---TEXT_END---")


def action_ui_state():
    """查询所有 UI 组件的当前状态"""
    result = api_request("GET", "/api/ui/state")
    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    import json
    print("SUCCESS: UI 状态查询成功")
    print("---STATE_START---")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("---STATE_END---")


def action_ui_set(component: str, value: str):
    """设置 UI 组件值"""
    if not component:
        print("ERROR: --component 参数不能为空", file=sys.stderr)
        sys.exit(1)
    if value is None:
        print("ERROR: --value 参数不能为空", file=sys.stderr)
        sys.exit(1)

    result = api_request("POST", "/api/ui/set", {
        "component": component,
        "value": value,
    })

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"SUCCESS: 已设置 {component} = {value}")


def action_add_avatar(video_path: str, avatar_name: str):
    """添加数字人"""
    if not video_path:
        print("ERROR: --video-path 参数不能为空", file=sys.stderr)
        sys.exit(1)
    if not avatar_name:
        print("ERROR: --avatar-name 参数不能为空", file=sys.stderr)
        sys.exit(1)

    print("PROGRESS: 正在提交添加数字人任务...")
    result = api_request("POST", "/api/add_avatar", {
        "video_path": video_path,
        "avatar_name": avatar_name,
    })

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    task_id = result["task_id"]
    print(f"PROGRESS: 任务已提交 (task_id: {task_id})，等待执行...")

    task_result = poll_task(task_id)
    print(f"SUCCESS: {task_result.get('message', '添加数字人完成')}")


def action_add_voice(audio_path: str, voice_name: str):
    """添加音色"""
    if not audio_path:
        print("ERROR: --audio-path 参数不能为空", file=sys.stderr)
        sys.exit(1)
    if not voice_name:
        print("ERROR: --voice-name 参数不能为空", file=sys.stderr)
        sys.exit(1)

    print("PROGRESS: 正在提交添加音色任务...")
    result = api_request("POST", "/api/add_voice", {
        "audio_path": audio_path,
        "voice_name": voice_name,
    })

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    task_id = result["task_id"]
    print(f"PROGRESS: 任务已提交 (task_id: {task_id})，等待执行...")

    task_result = poll_task(task_id)
    print(f"SUCCESS: {task_result.get('message', '添加音色完成')}")


def action_set_video(video_path: str):
    """设置本地视频路径"""
    if not video_path:
        print("ERROR: --video-path 参数不能为空", file=sys.stderr)
        sys.exit(1)

    result = api_request("POST", "/api/set_video", {"video_path": video_path})
    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)
    print(f"SUCCESS: {result.get('message', '视频路径已设置')}")


def action_set_cover(cover_path: str):
    """设置本地封面图片路径"""
    if not cover_path:
        print("ERROR: --cover-path 参数不能为空", file=sys.stderr)
        sys.exit(1)

    result = api_request("POST", "/api/set_cover", {"cover_path": cover_path})
    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)
    print(f"SUCCESS: {result.get('message', '封面路径已设置')}")


def action_search_douyin(keyword: str, max_count: int):
    """搜索抖音爆款视频"""
    if not keyword:
        print("ERROR: --keyword 参数不能为空", file=sys.stderr)
        sys.exit(1)

    print(f"PROGRESS: 正在搜索抖音视频，关键词: {keyword}，数量: {max_count}...")
    result = api_request("POST", "/api/search_douyin", {
        "keyword": keyword,
        "max_count": max_count,
    })

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    task_id = result["task_id"]
    print(f"PROGRESS: 任务已提交 (task_id: {task_id})，等待搜索完成...")

    task_result = poll_task(task_id)
    videos = task_result.get("result", {}).get("videos", [])
    count = task_result.get("result", {}).get("count", 0)

    print(f"SUCCESS: 搜索完成，共找到 {count} 个视频")
    print("---VIDEOS_START---")
    import json
    print(json.dumps(videos, ensure_ascii=False, indent=2))
    print("---VIDEOS_END---")


def main():
    parser = argparse.ArgumentParser(description="视频创作软件控制脚本")
    parser.add_argument(
        "--action", "-a",
        required=True,
        choices=[
            "ping", "login", "extract_text", "rewrite_text", "status",
            "generate_voice", "generate_video", "create_subtitle",
            "add_subtitle", "add_bgm", "generate_cover",
            "generate_title_tags", "publish", "execute_all",
            "ui_state", "ui_set",
            "refresh_avatars", "add_avatar", "delete_avatar",
            "refresh_voices", "add_voice", "delete_voice",
            "set_video", "set_cover",
            "search_douyin",
        ],
        help="要执行的操作"
    )
    parser.add_argument("--account", help="登录账号 (login 用)")
    parser.add_argument("--password", help="登录密码 (login 用)")
    parser.add_argument("--url", help="视频链接或本地路径 (extract_text 用)")
    parser.add_argument("--url-type", default="抖音分享链接", help="链接类型")
    parser.add_argument("--text", help="要改写的文案 (rewrite_text 用)")
    parser.add_argument("--mode", default="自动仿写", help="改写模式")
    parser.add_argument("--prompt", default="", help="自定义改写指令")
    parser.add_argument("--task-id", help="任务ID (status 用)")
    parser.add_argument("--component", help="UI 组件名称 (ui_set 用)")
    parser.add_argument("--value", help="UI 组件值 (ui_set 用)")
    parser.add_argument("--video-path", help="本地视频路径 (add_avatar/set_video 用)")
    parser.add_argument("--avatar-name", help="数字人名称 (add_avatar 用)")
    parser.add_argument("--audio-path", help="本地音频路径 (add_voice 用)")
    parser.add_argument("--voice-name", help="音色名称 (add_voice 用)")
    parser.add_argument("--cover-path", help="本地封面图片路径 (set_cover 用)")
    parser.add_argument("--keyword", help="搜索关键词 (search_douyin 用)")
    parser.add_argument("--max-count", type=int, default=9, help="最多获取视频数量 (search_douyin 用)")

    args = parser.parse_args()

    if args.action == "ping":
        action_ping()
    elif args.action == "login":
        action_login(args.account, args.password)
    elif args.action == "extract_text":
        action_extract_text(args.url, args.url_type)
    elif args.action == "rewrite_text":
        action_rewrite_text(args.text, args.mode, args.prompt)
    elif args.action == "status":
        action_status(args.task_id)
    elif args.action == "ui_state":
        action_ui_state()
    elif args.action == "ui_set":
        action_ui_set(args.component, args.value)
    elif args.action == "add_avatar":
        action_add_avatar(args.video_path, args.avatar_name)
    elif args.action == "add_voice":
        action_add_voice(args.audio_path, args.voice_name)
    elif args.action == "set_video":
        action_set_video(args.video_path)
    elif args.action == "set_cover":
        action_set_cover(args.cover_path)
    elif args.action == "search_douyin":
        action_search_douyin(args.keyword, args.max_count)
    elif args.action in (
        "generate_voice", "generate_video", "create_subtitle",
        "add_subtitle", "add_bgm", "generate_cover",
        "generate_title_tags", "publish", "execute_all",
        "refresh_avatars", "delete_avatar",
        "refresh_voices", "delete_voice",
    ):
        action_simple_trigger(args.action, f"/api/{args.action}")


if __name__ == "__main__":
    main()
