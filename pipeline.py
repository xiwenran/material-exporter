#!/usr/bin/env python3
"""
资料 → 图片 → 融景合成 一键流水线

流程：
  1. 扫描输入（文件夹 或 单个资料文件）中的支持文件
  2. 用 material-exporter 导出为 PNG 图片（存到 输出目录/资料图片/）
  3. 用融景对每组图片做透视合成（存到 输出目录/合成图/）

用法：
  python3 pipeline.py run --input <资料文件夹> --output <输出目录>
  python3 pipeline.py run --input <单个资料文件> --output <输出目录> --templates 3
  python3 pipeline.py run --input <资料文件夹> --output <输出目录> --max-slides 10
"""

import argparse
import json
import os
import subprocess
import sys

MATERIAL_EXPORTER_DIR = os.path.dirname(__file__)
RONGJING_DIR = os.path.expanduser("~/rongjing")


def run(cmd: list, desc: str) -> int:
    """运行子命令，实时打印输出，返回退出码。"""
    print(f"\n{'='*50}")
    print(f"▶ {desc}")
    print(f"{'='*50}")
    result = subprocess.run(cmd, cwd=os.path.dirname(cmd[1]) if len(cmd) > 1 else None)
    return result.returncode


def get_all_templates() -> list[str]:
    """从融景 CLI 获取所有可用模板名称。"""
    result = subprocess.run(
        ["python3", os.path.join(RONGJING_DIR, "cli.py"), "list-templates"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[错误] 无法获取融景模板列表：{result.stderr}", file=sys.stderr)
        sys.exit(1)
    templates = json.loads(result.stdout)
    # 只返回背景图存在的模板
    valid = [t["name"] for t in templates if t.get("background_exists", False)]
    if not valid:
        print("[错误] 没有找到有效的融景模板（背景图可能已移动或删除）", file=sys.stderr)
        sys.exit(1)
    return valid


def cmd_run(input_path: str, output_dir: str, templates: list[str] | None,
            max_slides: int, fmt: str):
    import shutil
    input_path = os.path.expanduser(input_path)
    output_dir = os.path.expanduser(output_dir)

    if not os.path.exists(input_path):
        print(f"[错误] 输入路径不存在：{input_path}", file=sys.stderr)
        sys.exit(1)

    # 单文件模式：不复制文件，直接用原始目录 + --only-file 过滤
    # （复制到新目录会触发 PowerPoint AppleScript 授权弹窗）
    only_file = None
    if os.path.isfile(input_path):
        only_file = os.path.basename(input_path)
        input_folder = os.path.dirname(os.path.abspath(input_path))
        print(f"单文件模式：{only_file}", flush=True)
    else:
        input_folder = input_path

    # 默认使用全部模板
    if not templates:
        print("未指定模板，正在获取融景全部可用模板...")
        templates = get_all_templates()
        print(f"将使用 {len(templates)} 个模板：{', '.join(templates)}")

    material_images_dir = os.path.join(output_dir, "资料图片")
    composed_dir = os.path.join(output_dir, "合成图")
    os.makedirs(material_images_dir, exist_ok=True)

    # ──────────────────────────────────────────
    # Step 1：资料 → 图片
    # ──────────────────────────────────────────
    convert_cmd = ["python3", os.path.join(MATERIAL_EXPORTER_DIR, "cli.py"), "convert",
                   "--input", input_folder,
                   "--output", material_images_dir,
                   "--max-slides", str(max_slides)]
    if only_file:
        convert_cmd += ["--only-file", only_file]

    rc = run(convert_cmd, f"Step 1 / 2  资料导出为图片（每个文件最多 {max_slides} 页）")
    if rc != 0:
        print("\n[错误] 资料转图片失败，流水线中止", file=sys.stderr)
        sys.exit(rc)

    # 找到所有导出成功的图片子文件夹
    image_subfolders = sorted([
        d for d in os.listdir(material_images_dir)
        if os.path.isdir(os.path.join(material_images_dir, d))
        and not d.startswith(".")
    ])

    if not image_subfolders:
        print("\n[错误] 资料转图片后没有找到任何输出文件夹", file=sys.stderr)
        sys.exit(1)

    print(f"\n导出了 {len(image_subfolders)} 组图片：{image_subfolders}")

    # ──────────────────────────────────────────
    # Step 2：图片 → 融景合成
    # ──────────────────────────────────────────
    total_groups = len(image_subfolders)
    for i, group in enumerate(image_subfolders, 1):
        group_input = os.path.join(material_images_dir, group)
        group_output = os.path.join(composed_dir, group)

        rc = run(
            ["python3", os.path.join(RONGJING_DIR, "cli.py"), "process",
             "--input", group_input,
             "--templates", *templates,
             "--output", group_output,
             "--format", fmt],
            f"Step 2 / 2  融景合成 [{i}/{total_groups}]：{group}"
        )
        if rc != 0:
            print(f"\n[警告] {group} 合成失败，继续处理下一组")

    # ──────────────────────────────────────────
    # 完成汇报
    # ──────────────────────────────────────────
    print(f"\n{'='*50}")
    print("✅ 流水线完成！")
    print(f"{'='*50}")
    print(f"资料图片：{material_images_dir}")
    print(f"合成结果：{composed_dir}")
    print(f"  ├ 组数：{total_groups}")
    print(f"  ├ 模板数：{len(templates)}")

    total_composed = sum(
        len(os.listdir(os.path.join(composed_dir, g, t)))
        for g in image_subfolders
        for t in (templates if os.path.isdir(os.path.join(composed_dir, g)) else [])
        if os.path.isdir(os.path.join(composed_dir, g, t))
    )
    print(f"  └ 合成图总数：约 {total_composed} 张")



def main():
    parser = argparse.ArgumentParser(description="资料 → 图片 → 融景合成 一键流水线")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("run", help="运行完整流水线")
    p.add_argument("--input", required=True, help="资料文件所在文件夹（递归扫描），或单个资料文件路径")
    p.add_argument("--output", required=True, help="输出根目录（自动创建 资料图片/ 和 合成图/ 子目录）")
    p.add_argument("--templates", nargs="+", default=None,
                   help="融景模板名称，不填则使用全部可用模板")
    p.add_argument("--max-slides", type=int, default=17,
                   help="每个文件最多导出页数（默认 17）")
    p.add_argument("--format", default="JPEG", choices=["PNG", "JPEG"],
                   help="合成图输出格式（默认 JPEG）")

    args = parser.parse_args()

    if args.cmd == "run":
        cmd_run(args.input, args.output, args.templates, args.max_slides, args.format)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
