"""Small reference filter; deliberately simple enough to inspect in one screen."""


def setup(context) -> None:  # noqa: ANN001
    def polish(output, hook_context):  # noqa: ANN001, ANN202
        config = context.config.read()
        replacements = config.get("replacements", {})
        if not isinstance(replacements, dict):
            return output
        narration = output.get("narration")
        if isinstance(narration, str):
            for source, target in replacements.items():
                if isinstance(source, str) and isinstance(target, str):
                    narration = narration.replace(source, target)
            output["narration"] = narration
        return output

    def count_turn(game, hook_context):  # noqa: ANN001, ANN202
        state = game.plugin_state.setdefault(context.plugin_id, {})
        state["commits"] = int(state.get("commits", 0)) + 1
        return game

    context.filter("narrator.output", polish)
    context.filter("turn.before_commit", count_turn)
