import asyncio
import os
import subprocess
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter

from backend.core.config import get_settings

router = APIRouter()


async def check_command_exists(command: str) -> bool:
    """Check if a command exists in the system PATH."""
    try:
        result = subprocess.run(
            ["which", command], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


async def check_claude_code() -> Dict[str, Any]:
    """Check if Claude Code is installed and configured."""
    result = {"installed": False, "configured": False, "version": None, "error": None}

    try:
        # Check if claude command exists
        if await check_command_exists("claude"):
            result["installed"] = True

            # Try to get version
            try:
                version_result = subprocess.run(
                    ["claude", "--version"], capture_output=True, text=True, timeout=5
                )
                if version_result.returncode == 0:
                    result["version"] = version_result.stdout.strip()
                    result["configured"] = True
            except Exception as e:
                result["error"] = f"Could not get Claude Code version: {str(e)}"
        else:
            result["error"] = "Claude Code not found in PATH"

    except Exception as e:
        result["error"] = str(e)

    return result


async def check_opencode() -> Dict[str, Any]:
    """Check if OpenCode is installed and configured."""
    result = {"installed": False, "configured": False, "version": None, "error": None}

    try:
        # Check if opencode command exists
        if await check_command_exists("opencode"):
            result["installed"] = True

            # Try to get version
            try:
                version_result = subprocess.run(
                    ["opencode", "--version"], capture_output=True, text=True, timeout=5
                )
                if version_result.returncode == 0:
                    result["version"] = version_result.stdout.strip()
                    result["configured"] = True
            except Exception as e:
                result["error"] = f"Could not get OpenCode version: {str(e)}"
        else:
            result["error"] = "OpenCode not found in PATH"

    except Exception as e:
        result["error"] = str(e)

    return result


async def check_elevenlabs() -> Dict[str, Any]:
    """Check if ElevenLabs is configured and accessible."""
    result = {
        "configured": False,
        "accessible": False,
        "error": None,
        "api_key_set": False,
    }

    settings = get_settings()

    try:
        # Check if API key is set
        if settings.elevenlabs_api_key:
            result["api_key_set"] = True
            result["configured"] = True

            # Try to make a test API call to ElevenLabs
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        "https://api.elevenlabs.io/v1/user",
                        headers={"xi-api-key": settings.elevenlabs_api_key},
                        timeout=10.0,
                    )

                    if response.status_code == 200:
                        result["accessible"] = True
                    elif response.status_code == 401:
                        result["error"] = "Invalid ElevenLabs API key"
                    else:
                        result[
                            "error"
                        ] = f"ElevenLabs API returned status {response.status_code}"

                except httpx.RequestError as e:
                    result["error"] = f"Could not connect to ElevenLabs API: {str(e)}"
        else:
            result["error"] = "ElevenLabs API key not configured"

    except Exception as e:
        result["error"] = str(e)

    return result


async def check_openai_tts() -> Dict[str, Any]:
    """Check if OpenAI TTS is configured and accessible."""
    result = {
        "configured": False,
        "accessible": False,
        "error": None,
        "api_key_set": False,
    }

    settings = get_settings()

    try:
        # Check if API key is set
        if settings.openai_api_key:
            result["api_key_set"] = True
            result["configured"] = True

            # Try to make a test API call to OpenAI
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                        timeout=10.0,
                    )

                    if response.status_code == 200:
                        result["accessible"] = True
                        # Check if TTS models are available
                        data = response.json()
                        tts_models = [
                            m
                            for m in data.get("data", [])
                            if "tts" in m.get("id", "").lower()
                        ]
                        if not tts_models:
                            result[
                                "error"
                            ] = "TTS models not available in OpenAI account"
                    elif response.status_code == 401:
                        result["error"] = "Invalid OpenAI API key"
                    else:
                        result[
                            "error"
                        ] = f"OpenAI API returned status {response.status_code}"

                except httpx.RequestError as e:
                    result["error"] = f"Could not connect to OpenAI API: {str(e)}"
        else:
            result["error"] = "OpenAI API key not configured"

    except Exception as e:
        result["error"] = str(e)

    return result


@router.get("/system-check")
async def system_check():
    """
    Comprehensive system check endpoint that validates all required services.
    Returns the status of each service and whether the system is ready.
    """

    # Run all checks in parallel
    results = await asyncio.gather(
        check_claude_code(),
        check_opencode(),
        check_elevenlabs(),
        check_openai_tts(),
        return_exceptions=True,
    )

    # Handle any exceptions that occurred during checks
    claude_code_status = (
        results[0]
        if not isinstance(results[0], Exception)
        else {"error": str(results[0])}
    )
    opencode_status = (
        results[1]
        if not isinstance(results[1], Exception)
        else {"error": str(results[1])}
    )
    elevenlabs_status = (
        results[2]
        if not isinstance(results[2], Exception)
        else {"error": str(results[2])}
    )
    openai_status = (
        results[3]
        if not isinstance(results[3], Exception)
        else {"error": str(results[3])}
    )

    # Determine if system meets minimum requirements
    has_ai_cli = (
        claude_code_status.get("installed") and claude_code_status.get("configured")
    ) or (opencode_status.get("installed") and opencode_status.get("configured"))

    has_tts = (
        elevenlabs_status.get("configured") and elevenlabs_status.get("accessible")
    ) or (openai_status.get("configured") and openai_status.get("accessible"))

    system_ready = has_ai_cli and has_tts

    # Prepare response with detailed status and recommendations
    response = {
        "system_ready": system_ready,
        "requirements_met": {"ai_cli": has_ai_cli, "tts_service": has_tts},
        "services": {
            "claude_code": claude_code_status,
            "opencode": opencode_status,
            "elevenlabs": elevenlabs_status,
            "openai_tts": openai_status,
        },
        "recommendations": [],
    }

    # Add recommendations based on status
    if not has_ai_cli:
        if not claude_code_status.get("installed") and not opencode_status.get(
            "installed"
        ):
            response["recommendations"].append(
                "Install either Claude Code (recommended) or OpenCode CLI tool"
            )
        elif claude_code_status.get("installed") and not claude_code_status.get(
            "configured"
        ):
            response["recommendations"].append(
                "Configure Claude Code by running: claude login"
            )
        elif opencode_status.get("installed") and not opencode_status.get("configured"):
            response["recommendations"].append(
                "Configure OpenCode by setting up your API credentials"
            )

    if not has_tts:
        if not elevenlabs_status.get("api_key_set") and not openai_status.get(
            "api_key_set"
        ):
            response["recommendations"].append(
                "Set either ELEVENLABS_API_KEY or OPENAI_API_KEY environment variable"
            )
        elif elevenlabs_status.get("api_key_set") and not elevenlabs_status.get(
            "accessible"
        ):
            response["recommendations"].append(
                f"Fix ElevenLabs configuration: {elevenlabs_status.get('error')}"
            )
        elif openai_status.get("api_key_set") and not openai_status.get("accessible"):
            response["recommendations"].append(
                f"Fix OpenAI configuration: {openai_status.get('error')}"
            )

    return response


@router.get("/system-check/quick")
async def quick_system_check():
    """
    Quick system check that only verifies if minimum requirements are met.
    Faster than the comprehensive check.
    """
    settings = get_settings()

    # Quick checks without API calls
    claude_installed = await check_command_exists("claude")
    opencode_installed = await check_command_exists("opencode")

    has_ai_cli = claude_installed or opencode_installed
    has_tts = bool(settings.elevenlabs_api_key or settings.openai_api_key)

    return {
        "system_ready": has_ai_cli and has_tts,
        "has_ai_cli": has_ai_cli,
        "has_tts": has_tts,
    }
