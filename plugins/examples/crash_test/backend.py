def setup(context) -> None:  # noqa: ANN001
    def crash(game, hook_context):  # noqa: ANN001, ANN202
        game.plugin_state[context.plugin_id] = {"must_not_commit": True}
        raise RuntimeError("intentional reference-plugin crash")

    context.filter("turn.before_commit", crash)
