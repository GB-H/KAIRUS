"""
Testes para ai/memory.py — gerenciador de memoria.
"""

import pytest
from ai.memory import ConversationMemory, get_memory, clear_memory


class TestConversationMemory:

    def test_add_message(self):
        mem = ConversationMemory("test_session_1")
        mem.add_message("user", "oi")
        assert len(mem.messages) == 1
        assert mem.messages[0]["role"] == "user"
        assert mem.messages[0]["content"] == "oi"

    def test_message_count(self):
        mem = ConversationMemory("test_session_2")
        mem.add_message("user", "oi")
        mem.add_message("assistant", "ola")
        assert mem.message_count == 2

    def test_user_info(self):
        mem = ConversationMemory("test_session_3")
        mem.set_user_info("name", "Gabriel")
        assert mem.get_user_info("name") == "Gabriel"

    def test_user_info_not_found(self):
        mem = ConversationMemory("test_session_4")
        assert mem.get_user_info("name") is None

    def test_topics(self):
        mem = ConversationMemory("test_session_5")
        mem.add_topic("greeting")
        mem.add_topic("identity")
        assert mem.has_discussed("greeting") is True
        assert mem.has_discussed("unknown_topic") is False

    def test_no_duplicate_topics(self):
        mem = ConversationMemory("test_session_6")
        mem.add_topic("greeting")
        mem.add_topic("greeting")
        assert len(mem.topics_discussed) == 1

    def test_recent_messages(self):
        mem = ConversationMemory("test_session_7")
        for i in range(10):
            mem.add_message("user", f"msg {i}")
        recent = mem.get_recent_messages(3)
        assert len(recent) == 3
        assert recent[-1]["content"] == "msg 9"

    def test_context_summary(self):
        mem = ConversationMemory("test_session_8")
        mem.set_user_info("name", "Gabriel")
        mem.add_topic("greeting")
        summary = mem.get_context_summary()
        assert "Gabriel" in summary
        assert "greeting" in summary

    def test_clear(self):
        mem = ConversationMemory("test_session_9")
        mem.add_message("user", "oi")
        mem.set_user_info("name", "Gabriel")
        mem.clear()
        assert len(mem.messages) == 0
        assert mem.get_user_info("name") is None


class TestMemoryManager:

    def test_get_memory_creates(self):
        mem = get_memory("test_mgr_1")
        assert isinstance(mem, ConversationMemory)

    def test_get_memory_returns_same(self):
        mem1 = get_memory("test_mgr_2")
        mem2 = get_memory("test_mgr_2")
        assert mem1 is mem2

    def test_clear_memory(self):
        get_memory("test_mgr_3")
        clear_memory("test_mgr_3")
        from ai.memory import _active_memories
        assert "test_mgr_3" not in _active_memories