"""
API密钥检查工具
"""

import os


# 占位符列表（识别未配置的占位符值）
_PLACEHOLDER_PREFIXES = ("your_", "your-")
_PLACEHOLDER_SUFFIXES = ("_here", "-here")


def _is_real_key(value: str | None) -> bool:
    """判断是否为真实密钥（非空、非占位符）"""
    if not value:
        return False
    stripped = value.strip()
    if not stripped:
        return False
    lowered = stripped.lower()
    if any(lowered.startswith(prefix) for prefix in _PLACEHOLDER_PREFIXES):
        return False
    if any(lowered.endswith(suffix) for suffix in _PLACEHOLDER_SUFFIXES):
        return False
    return True


def check_api_keys(provider: str | None = None, market_type: str | None = None):
    """检查所有必要的API密钥是否已配置

    Args:
        provider: 当前选择的 LLM 提供商（如 'deepseek'、'dashscope'）。
                  仅用于在提示信息中显示当前选择。
        market_type: 当前分析的市场类型（'美股'/'A股'/'港股'）。
                     FINNHUB 仅在分析美股时必需。

    策略：DEEPSEEK_API_KEY 是系统**强制必需**的 LLM 密钥，无论选择哪个
    提供商都必须配置（用于核心分析与记忆嵌入）。其他 LLM 密钥仅作为提示，
    不会被当作启动阻断条件。
    """

    # 检查各个API密钥
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    finnhub_key = os.getenv("FINNHUB_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    qianfan_key = os.getenv("QIANFAN_API_KEY")

    provider_norm = (provider or "").strip().lower()
    # 仅用于诊断显示；不再影响"必需"判定
    _ = provider_norm

    # 兼容性保留参数（FINNHUB 改为完全可选：未配置时主页面仍可进入，
    #          美股分析时会降级到备用数据源并在日志中给出警告）
    _ = (market_type or "").strip() == "美股"

    # DEEPSEEK 是强制必需的（无论选择哪个 LLM 提供商）
    deepseek_needed = True

    # FINNHUB 改为完全可选（核心 LLM 由 DEEPSEEK 提供；FINNHUB 缺失时数据层会自动降级）
    finnhub_needed = False

    # 构建详细状态
    details = {
        "DASHSCOPE_API_KEY": {
            "configured": _is_real_key(dashscope_key),
            "display": f"{dashscope_key[:12]}..." if dashscope_key else "未配置",
            "required": False,
            "description": "阿里百炼API密钥（可选；不配置时记忆功能会自动降级）"
        },
        "DEEPSEEK_API_KEY": {
            "configured": _is_real_key(deepseek_key),
            "display": f"{deepseek_key[:12]}..." if deepseek_key else "未配置",
            "required": deepseek_needed,
            "description": "DeepSeek API密钥（系统强制必需；用于核心分析与嵌入回退）"
        },
        "FINNHUB_API_KEY": {
            "configured": _is_real_key(finnhub_key),
            "display": f"{finnhub_key[:12]}..." if finnhub_key else "未配置",
            "required": finnhub_needed,
            "description": "金融数据API密钥（可选；缺失时美股分析会自动降级到备用数据源）"
        },
        "OPENAI_API_KEY": {
            "configured": _is_real_key(openai_key),
            "display": f"{openai_key[:12]}..." if openai_key else "未配置",
            "required": False,
            "description": "OpenAI API密钥（可选）"
        },
        "ANTHROPIC_API_KEY": {
            "configured": _is_real_key(anthropic_key),
            "display": f"{anthropic_key[:12]}..." if anthropic_key else "未配置",
            "required": False,
            "description": "Anthropic API密钥（可选）"
        },
        "GOOGLE_API_KEY": {
            "configured": _is_real_key(google_key),
            "display": f"{google_key[:12]}..." if google_key else "未配置",
            "required": False,
            "description": "Google AI API密钥（可选）"
        },
        "QIANFAN_ACCESS_KEY": {
            "configured": _is_real_key(qianfan_key),
            "display": f"{qianfan_key[:16]}..." if qianfan_key else "未配置",
            "required": False,
            "description": "文心一言（千帆）API Key（可选），一般以 bce-v3/ 开头"
        },
    }

    # 检查必需的API密钥
    missing_required = [
        key for key, info in details.items()
        if info["required"] and not info["configured"]
    ]

    return {
        "all_configured": len(missing_required) == 0,
        "required_configured": len(missing_required) == 0,
        "missing_required": missing_required,
        "details": details,
        "summary": {
            "total": len(details),
            "configured": sum(1 for info in details.values() if info["configured"]),
            "required": sum(1 for info in details.values() if info["required"]),
            "required_configured": sum(
                1 for info in details.values()
                if info["required"] and info["configured"]
            )
        }
    }

def get_api_key_status_message():
    """获取API密钥状态消息"""

    status = check_api_keys()

    if status["all_configured"]:
        return "✅ 所有必需的API密钥已配置完成"
    elif status["required_configured"]:
        return "✅ 必需的API密钥已配置，可选API密钥未配置"
    else:
        missing = ", ".join(status["missing_required"])
        return f"❌ 缺少必需的API密钥: {missing}"

def validate_api_key_format(key_type, api_key):
    """验证API密钥格式"""
    
    if not api_key:
        return False, "API密钥不能为空"
    
    # 基本长度检查
    if len(api_key) < 10:
        return False, "API密钥长度过短"
    
    # 特定格式检查
    if key_type == "DASHSCOPE_API_KEY":
        if not api_key.startswith("sk-"):
            return False, "阿里百炼API密钥应以'sk-'开头"
    elif key_type == "OPENAI_API_KEY":
        if not api_key.startswith("sk-"):
            return False, "OpenAI API密钥应以'sk-'开头"
    elif key_type == "QIANFAN_API_KEY":
        if not api_key.startswith("bce-v3/"):
            return False, "千帆 API Key（OpenAI兼容）应以 'bce-v3/' 开头"
    
    return True, "API密钥格式正确"

def test_api_connection(key_type, api_key):
    """测试API连接（简单验证）"""
    
    # 这里可以添加实际的API连接测试
    # 为了简化，现在只做格式验证
    
    is_valid, message = validate_api_key_format(key_type, api_key)
    
    if not is_valid:
        return False, message
    
    # 可以在这里添加实际的API调用测试
    # 例如：调用一个简单的API端点验证密钥有效性
    
    return True, "API密钥验证通过"
