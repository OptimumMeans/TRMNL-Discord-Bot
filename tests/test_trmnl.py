import pytest
import discord
from discord import app_commands
from unittest.mock import AsyncMock, MagicMock, patch
import json
from pathlib import Path
from src.bot.trmnl import TRMNL

@pytest.fixture
def bot():
    bot = MagicMock()
    bot.tree = MagicMock()
    bot.tree.sync = AsyncMock()
    return bot

@pytest.fixture
def cog(bot):
    return TRMNL(bot)

@pytest.fixture
def interaction():
    interaction = AsyncMock()
    interaction.response = AsyncMock()
    interaction.response.send_message = AsyncMock()
    return interaction

@pytest.mark.asyncio
async def test_sync_command(cog, interaction):
    # Setup
    cog.handle_rate_limit = AsyncMock(return_value=True)
    cog.bot.tree.sync.return_value = ["command1", "command2"]

    # Execute
    await cog.sync.callback(cog, interaction)

    # Verify
    assert interaction.followup.send.called
    args = interaction.followup.send.call_args[1]
    assert "Successfully synced 2 commands" in args["embed"].description

@pytest.mark.asyncio
async def test_home_command(cog, interaction):
    # Setup
    cog.handle_rate_limit = AsyncMock(return_value=True)
    
    # Execute
    await cog.home.callback(cog, interaction)

    # Verify
    assert interaction.response.send_message.called
    args = interaction.response.send_message.call_args[1]
    assert isinstance(args["embed"], discord.Embed)
    assert args["embed"].title == "TRMNL Resources"

@pytest.mark.asyncio
async def test_rate_limit_block(cog, interaction):
    # Setup
    cog.handle_rate_limit = AsyncMock(return_value=False)
    
    # Execute
    await cog.home.callback(cog, interaction)

    # Verify command was blocked due to rate limit
    assert not interaction.response.send_message.called

@pytest.mark.asyncio
async def test_reload_docs(cog, interaction):
    # Setup
    cog.handle_rate_limit = AsyncMock(return_value=True)
    original_docs = cog.docs_data.copy()
    
    # Execute
    await cog.reload_docs_command.callback(cog, interaction)
    
    # Verify
    assert interaction.response.send_message.called
    args = interaction.response.send_message.call_args[1]
    assert isinstance(args["embed"], discord.Embed)
    assert "Successfully reloaded" in args["embed"].description

@pytest.mark.asyncio
async def test_error_handling(cog, interaction):
    # Setup
    async def raise_error(*args, **kwargs):
        raise Exception("Test error")
    cog.handle_rate_limit = AsyncMock(side_effect=raise_error)

    # Execute
    await cog.home.callback(cog, interaction)

    # Verify
    assert interaction.followup.send.called
    args = interaction.followup.send.call_args
    assert "error occurred" in args[0][0].lower()
    assert args[1]["ephemeral"] is True

@pytest.mark.asyncio
async def test_docs_command(cog, interaction):
    # Setup
    cog.handle_rate_limit = AsyncMock(return_value=True)
    
    # Execute
    await cog.docs.callback(cog, interaction)
    
    # Verify
    assert interaction.response.send_message.called
    args = interaction.response.send_message.call_args[1]
    assert isinstance(args["embed"], discord.Embed)
    assert "Documentation" in args["embed"].title

@pytest.mark.asyncio
async def test_framework_command(cog, interaction):
    # Setup
    cog.handle_rate_limit = AsyncMock(return_value=True)
    
    # Execute
    await cog.framework.callback(cog, interaction)
    
    # Verify
    assert interaction.response.send_message.called
    args = interaction.response.send_message.call_args[1]
    assert isinstance(args["embed"], discord.Embed)
    assert "Framework" in args["embed"].title

@pytest.mark.asyncio
async def test_privacy_command(cog, interaction):
    # Setup
    cog.handle_rate_limit = AsyncMock(return_value=True)
    
    # Execute
    await cog.privacy.callback(cog, interaction)
    
    # Verify
    assert interaction.response.send_message.called
    args = interaction.response.send_message.call_args[1]
    assert isinstance(args["embed"], discord.Embed)

@pytest.mark.asyncio
async def test_file_not_found_error(cog, interaction):
    # Setup
    cog.load_docs = MagicMock(side_effect=FileNotFoundError("docs.json not found"))
    cog.handle_rate_limit = AsyncMock(return_value=True)
    cog.handle_command_error = AsyncMock()  # Mock error handler

    # Execute
    await cog.reload_docs_command.callback(cog, interaction)

    # Verify handle_command_error was called
    cog.handle_command_error.assert_called_once()
    error_args = cog.handle_command_error.call_args[0]
    assert interaction in error_args
    assert isinstance(error_args[1], FileNotFoundError)

@pytest.mark.asyncio
async def test_terms_command(cog, interaction):
    # Setup
    cog.handle_rate_limit = AsyncMock(return_value=True)
    
    # Execute
    await cog.terms.callback(cog, interaction)
    
    # Verify
    assert interaction.response.send_message.called
    args = interaction.response.send_message.call_args[1]
    assert isinstance(args["embed"], discord.Embed)

@pytest.mark.asyncio
async def test_rate_limit_handling(cog, interaction):
    # Setup - simulate rate limit exceeded
    cog.handle_rate_limit = AsyncMock(return_value=False)
    
    # Execute
    for cmd in [cog.home, cog.docs, cog.framework, cog.privacy, cog.terms]:
        await cmd.callback(cog, interaction)
        assert not interaction.response.send_message.called
        interaction.response.send_message.reset_mock()

@pytest.mark.asyncio
async def test_news_command(cog, interaction):
    # Setup
    cog.handle_rate_limit = AsyncMock(return_value=True)
    
    # Execute
    await cog.news.callback(cog, interaction)
    
    # Verify
    assert interaction.response.send_message.called
    args = interaction.response.send_message.call_args[1]
    assert isinstance(args["embed"], discord.Embed)
    assert "Latest Updates" in args["embed"].title

@pytest.mark.asyncio
async def test_updates_command(cog, interaction):
    # Setup
    cog.handle_rate_limit = AsyncMock(return_value=True)
    
    # Execute
    await cog.updates.callback(cog, interaction)
    
    # Verify
    assert interaction.response.send_message.called
    args = interaction.response.send_message.call_args[1]
    assert isinstance(args["embed"], discord.Embed)
    assert "TRMNL Updates" in args["embed"].title

@pytest.mark.asyncio
async def test_diy_command(cog, interaction):
    # Setup
    cog.handle_rate_limit = AsyncMock(return_value=True)
    
    # Execute
    await cog.diy.callback(cog, interaction)
    
    # Verify
    assert interaction.response.send_message.called
    args = interaction.response.send_message.call_args[1]
    assert isinstance(args["embed"], discord.Embed)
    assert "DIY TRMNL" in args["embed"].title