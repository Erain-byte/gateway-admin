"""
密钥生成工具

用于生成安全的 HMAC_SECRET_KEY
"""

import secrets
import argparse


def generate_secret_key(length: int = 32) -> str:
    """
    生成安全的随机密钥
    
    Args:
        length: 密钥长度（字节），默认32字节（256位）
    
    Returns:
        URL安全的Base64编码字符串
    """
    return secrets.token_urlsafe(length)


def main():
    parser = argparse.ArgumentParser(description="生成安全的密钥")
    parser.add_argument(
        "-l", "--length",
        type=int,
        default=32,
        help="密钥长度（字节），默认32"
    )
    parser.add_argument(
        "-c", "--copy",
        action="store_true",
        help="复制到剪贴板（需要 pyperclip 库）"
    )
    
    args = parser.parse_args()
    
    key = generate_secret_key(args.length)
    
    print("=" * 60)
    print("生成的密钥：")
    print(key)
    print("=" * 60)
    print(f"\n使用方法：")
    print(f"1. 将密钥添加到 .env 文件：")
    print(f"   HMAC_SECRET_KEY={key}")
    print(f"\n2. 或设置为环境变量：")
    print(f"   export HMAC_SECRET_KEY='{key}'")
    
    if args.copy:
        try:
            import pyperclip
            pyperclip.copy(key)
            print("\n✅ 密钥已复制到剪贴板！")
        except ImportError:
            print("\n⚠️  未安装 pyperclip 库，无法复制到剪贴板")
            print("   安装命令: pip install pyperclip")


if __name__ == "__main__":
    main()