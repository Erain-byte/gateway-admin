"""
路径匹配工具

支持通配符匹配，用于公开路径白名单验证
"""
import fnmatch
from typing import List

def is_public_path(path: str, public_patterns: List[str]) -> bool:

    for pattern in public_patterns:
        if fnmatch.fnmatchcase(path, pattern):
            return True
    return False

def parse_public_paths(config_string: str) -> List[str]:
      if not config_string:
        return []
      return [path.strip() for path in config_string.split(",") if path.strip()]
