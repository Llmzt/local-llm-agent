"""提供命令行聊天入口，维护对话历史并调用 Agent。"""

from service.core.errors import AppError
from service.core.logger import get_logger

from agent import (
    add_assistant_message,
    add_user_message,
    create_history,
    run_agent,
    trim_history,
)

logger = get_logger(__name__)

# 启动交互式循环，读取用户问题、调用 Agent、保存多轮对话历史。
def main():
    """命令行入口：维护多轮对话历史并调用 Agent。"""

    logger.info("CLI started")

    messages = create_history()

    while True:
        messages = trim_history(messages)

        user_input = input("\n你：").strip()
        if not user_input:
            logger.warning("empty user input")
            print("user_input 不能为空")
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            logger.info("CLI exited by user")
            print("已退出")
            break

        add_user_message(messages, user_input)

        print("助手：", end="")
        try:
            reply = run_agent(messages, stream=True, stream_print=True)
            print()
        except AppError as exc:
            logger.exception("handled application error")
            reply = exc.user_message
            print(reply)
        except Exception:
            logger.exception("unexpected error")
            reply = "程序发生未知错误，请查看日志。"
            print(reply)

        add_assistant_message(messages, reply)
if __name__ == "__main__":
    main()
