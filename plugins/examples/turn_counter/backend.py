"""Minimal stateful filter used by core plugin-lifecycle tests."""


def setup(context) -> None:  # noqa: ANN001
    def count_turn(game, hook_context):  # noqa: ANN001, ANN202, ARG001
        state = game.plugin_state.setdefault(context.plugin_id, {})
        state["commits"] = int(state.get("commits", 0)) + 1
        return game

    context.filter("turn.before_commit", count_turn)
