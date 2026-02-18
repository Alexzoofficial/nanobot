"""Configuration loading utilities."""

import json
import os
from pathlib import Path
from typing import Any

from nanobot.config.schema import Config


def get_config_path() -> Path:
    """Get the default configuration file path."""
    return Path.home() / ".nanobot" / "config.json"


def get_data_dir() -> Path:
    """Get the nanobot data directory."""
    from nanobot.utils.helpers import get_data_path
    return get_data_path()


def load_config(config_path: Path | None = None) -> Config:
    """
    Load configuration from environment variable, file, or create default.

    Priority:
    1. NANOBOT_CONFIG environment variable (JSON string)
    2. Explicitly provided config_path
    3. ~/.nanobot/config.json
    4. ./config.json (current directory)
    
    Args:
        config_path: Optional path to config file.
    
    Returns:
        Loaded configuration object.
    """
    config = None

    # 1. Try NANOBOT_CONFIG environment variable
    env_config = os.environ.get("NANOBOT_CONFIG")
    if env_config:
        try:
            data = json.loads(env_config)
            data = _migrate_config(data)
            config = Config.model_validate(convert_keys(data))
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Failed to load config from NANOBOT_CONFIG: {e}")

    # 2. Try file paths
    if config is None:
        paths = []
        if config_path:
            paths.append(config_path)
        else:
            paths.append(get_config_path())
            paths.append(Path("config.json"))

        for path in paths:
            if path.exists():
                try:
                    with open(path) as f:
                        data = json.load(f)
                    data = _migrate_config(data)
                    config = Config.model_validate(convert_keys(data))
                    break
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Warning: Failed to load config from {path}: {e}")
                    continue

    if config is None:
        config = Config()

    return _apply_env_overrides(config)


def _apply_env_overrides(config: Config) -> Config:
    """Apply flat environment variable overrides for easy deployment."""
    # LLM Providers
    if key := os.environ.get("GROQ_API_KEY") or os.environ.get("LITELLM_GROQ_API_KEY"):
        config.providers.groq.api_key = key
    if key := os.environ.get("OPENROUTER_API_KEY"):
        config.providers.openrouter.api_key = key
    if key := os.environ.get("OPENAI_API_KEY"):
        config.providers.openai.api_key = key
    if key := os.environ.get("ANTHROPIC_API_KEY"):
        config.providers.anthropic.api_key = key
    if key := os.environ.get("DEEPSEEK_API_KEY"):
        config.providers.deepseek.api_key = key
    if key := os.environ.get("GEMINI_API_KEY"):
        config.providers.gemini.api_key = key
    if key := os.environ.get("ZHIPU_API_KEY") or os.environ.get("ZHIPUAI_API_KEY"):
        config.providers.zhipu.api_key = key

    # Agent
    if model := os.environ.get("AGENT_MODEL") or os.environ.get("MODEL"):
        config.agents.defaults.model = model
    if workspace := os.environ.get("AGENT_WORKSPACE"):
        config.agents.defaults.workspace = workspace
    if os.environ.get("AGENT_ENGINE"):
        # We don't have a direct engine field, it's inferred from the model,
        # but some users might expect it.
        pass

    # Telegram
    if token := os.environ.get("TELEGRAM_TOKEN"):
        config.channels.telegram.token = token
        config.channels.telegram.enabled = True

    if allowed := os.environ.get("ALLOWED_USERS") or os.environ.get("TELEGRAM_ALLOWED_USERS"):
        # Split by comma and strip whitespace
        users = [u.strip() for u in allowed.split(",")]
        config.channels.telegram.allow_from = users

    # WhatsApp (basic support via env)
    if os.environ.get("WHATSAPP_ENABLED", "").lower() == "true":
        config.channels.whatsapp.enabled = True
    if wa_allow := os.environ.get("WHATSAPP_ALLOWED_NUMBERS"):
        config.channels.whatsapp.allow_from = [n.strip() for n in wa_allow.split(",")]

    # Generic CHANNELS env var (e.g. CHANNELS=telegram,whatsapp)
    if channels_env := os.environ.get("CHANNELS"):
        enabled_list = [c.strip().lower() for c in channels_env.split(",")]
        for c in enabled_list:
            if hasattr(config.channels, c):
                getattr(config.channels, c).enabled = True

    # Web Tools
    if alexzo_key := os.environ.get("ALEXZO_API_KEY"):
        config.tools.web.search.api_key = alexzo_key

    return config


def save_config(config: Config, config_path: Path | None = None) -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration to save.
        config_path: Optional path to save to. Uses default if not provided.
    """
    path = config_path or get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to camelCase format
    data = config.model_dump()
    data = convert_to_camel(data)
    
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _migrate_config(data: dict) -> dict:
    """Migrate old config formats to current."""
    # Move tools.exec.restrictToWorkspace → tools.restrictToWorkspace
    tools = data.get("tools", {})
    exec_cfg = tools.get("exec", {})
    if "restrictToWorkspace" in exec_cfg and "restrictToWorkspace" not in tools:
        tools["restrictToWorkspace"] = exec_cfg.pop("restrictToWorkspace")
    return data


def convert_keys(data: Any) -> Any:
    """Convert camelCase keys to snake_case for Pydantic."""
    if isinstance(data, dict):
        return {camel_to_snake(k): convert_keys(v) for k, v in data.items()}
    if isinstance(data, list):
        return [convert_keys(item) for item in data]
    return data


def convert_to_camel(data: Any) -> Any:
    """Convert snake_case keys to camelCase."""
    if isinstance(data, dict):
        return {snake_to_camel(k): convert_to_camel(v) for k, v in data.items()}
    if isinstance(data, list):
        return [convert_to_camel(item) for item in data]
    return data


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result.append("_")
        result.append(char.lower())
    return "".join(result)


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])
